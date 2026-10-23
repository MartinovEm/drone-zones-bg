#!/usr/bin/env python3
"""Weekly check of the official texts the „Правила“ pop-up links to (ROADMAP 9, owner 23.10.2026).

Every watched source is fetched once and its fingerprint compared with tools/rules_sources.json:
a PDF by its bytes, a page by its main text and the PDF documents it links to (the pages carry
per-request codes, so a whole-page hash would always differ), lex.bg by its list of amendments.
A changed fingerprint or a dead link (404 / 410) fails the run, so GitHub e-mails the repository
owner; the log names what changed. A source that does not answer (network error, 5xx), or answers
without the document's own content (a bot check or consent page: no PDF, no <article> / <main>
text, no amendment list), is only a ::warning - nothing is known to have changed. The panel's „Сверено с официалните текстове на
<дата>“ never moves by itself: after a real re-check of the changed text, refresh the stored
fingerprints with  python tools/rules_watch.py --update  and commit tools/rules_sources.json.

Not watched: EUR-Lex refuses programs (HTTP 202 with an empty body, a bot check) - EASA's Easy
Access Rules for UAS stand in for Regulation 2019/947; the Държавен вестник issue pages never
change (an amendment is a new issue: the CAA's consolidated text and lex.bg show it); uas.caa.bg
is an app, not a text. Standard library only.

  python tools/rules_watch.py                       check (exit 1 on a change or a dead link)
  python tools/rules_watch.py --update              store the current fingerprints
  ... --fixtures DIR  read <key>.bin + <key>.json saved copies instead of the network (tests)
  ... --json FILE     another fingerprint file (tests)
"""
import hashlib, html, json, os, re, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CAA = "https://www.caa.bg"
FORM = (CAA + "/sites/default/files/uploads/%D0%97%D0%B0%D1%8F%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5"
        "%20%D0%91%D0%9B%D0%A1%20%D0%B7%D0%BE%D0%BD%D0%B8%20%D0%B8%20%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D0%B8%D1%80"
        "%D0%B0%D0%BD%D0%B5%20%D0%BD%D0%B0%20%D0%92%D0%9F%2004.2026.pdf")
# (key, kind, url, what it is) - the panel's links (tools/rules_panel.py) + the CAA's Н-6 page,
# which lists the current consolidated text, + EASA's Easy Access Rules (for EUR-Lex)
SOURCES = [
    ("n6pdf", "pdf", CAA + "/sites/default/files/upload/documents/2026-01/%D0%9D%D0%A0_2023_664891.2025114.pdf", "Наредба № Н-6, обединен текст (ГВА, PDF)"),
    ("caan6", "page", CAA + "/bg/category/246/23167", "Наредба № Н-6 - страницата на ГВА с текущия обединен текст"),
    ("zgvpdf", "pdf", CAA + "/sites/default/files/upload/documents/2026-04/%D0%97%D0%93%D0%92%D1%8A%D0%B7%D0%B4_1972.2026032.pdf", "Закон за гражданското въздухоплаване, обединен текст (ГВА, PDF)"),
    ("formpdf", "pdf", FORM, "Заявление за полети в географски зони / резервиране (ГВА, PDF)"),
    ("caa633", "page", CAA + "/bg/category/633", "ГВА - раздел „Безпилотни летателни системи“"),
    ("caa29602", "page", CAA + "/bg/category/899/29602", "ГВА - „Искам да управлявам дрон“: обща информация"),
    ("caa29604", "page", CAA + "/bg/category/899/29604", "ГВА - кога се изисква регистрация и сертификат"),
    ("caa29605", "page", CAA + "/bg/category/899/29605", "ГВА - често задавани въпроси"),
    ("easaear", "pdf", "https://www.easa.europa.eu/en/downloads/110913/en", "EASA Easy Access Rules for UAS (вместо EUR-Lex)"),
    ("easaop", "page", "https://www.easa.europa.eu/en/document-library/opinions/opinion-no-062026", "EASA Opinion 06/2026"),
    ("faq116467", "page", "https://www.easa.europa.eu/en/faq/116467", "EASA FAQ 116467 (operator)"),
    ("faq116468", "page", "https://www.easa.europa.eu/en/faq/116468", "EASA FAQ 116468 (remote pilot)"),
    ("faq116510", "page", "https://www.easa.europa.eu/en/faq/116510", "EASA FAQ 116510 (drone racing)"),
    ("faq116511", "page", "https://www.easa.europa.eu/en/faq/116511", "EASA FAQ 116511 (FPV goggles)"),
    ("faq140037", "page", "https://www.easa.europa.eu/en/faq/140037", "EASA FAQ 140037 (BVLOS / FPV)"),
    ("crc2587", "page", "https://crc.bg/bg/statii/2587/pravila-za-svobodno-izpolzvane-na-radiochestotniq-spektar", "КРС - Правила за свободно използване на радиочестотния спектър"),
    ("crc2480", "page", "https://crc.bg/bg/statii/2480/prilojenie-2-ustroystva-s-malak-obseg-na-deystvie", "КРС - Приложение 2 (устройства с малък обсег)"),
    ("crcham", "pdf", "https://crc.bg/files/2025%20%D0%9F%D0%A0%D0%90%D0%92%D0%9D%D0%90/Pravila_radiolubiteli.pdf", "КРС - Правила за радиолюбителите (PDF)"),
    ("cept7003", "pdf", "https://docdb.cept.org/download/4980", "CEPT ERC/REC 70-03 (PDF)"),
    ("lexzzt", "lex", "https://www.lex.bg/laws/ldoc/2134445060", "Закон за защитените територии - изменения (lex.bg)"),
]
HEADERS = {"User-Agent": "bgr-drone-zones rules watch (https://martinovem.github.io/drone-zones-bg/)", "Accept-Language": "bg,en;q=0.8"}


def fetch(url):
    """(status, body, headers); status 0 = no answer. Retried twice, 15 s apart, like the sources watchdog."""
    last = (0, b"", {"error": "no attempt"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            last = (e.code, e.read() or b"", dict(e.headers or {}))
            if e.code < 500:
                return last  # a 4xx is an answer, not a hiccup
        except Exception as e:  # network error / timeout
            last = (0, b"", {"error": repr(e)[:200]})
        if attempt < 2:
            time.sleep(15)
    return last


def strip_html(s):
    s = re.sub(r"(?is)<(script|style|noscript|svg|form|template|button)\b.*?</\1>", " ", s)
    s = re.sub(r"(?is)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def main_region(s):
    """The page's own content: its <article>, else its <main> (both sites' menus, footers and scripts left out); None if it has neither."""
    for tag in ("article", "main"):
        a, b = s.find("<" + tag), s.rfind("</" + tag + ">")
        if a >= 0 and b > a:
            return s[a:b]
    return None


def fingerprint(kind, body):
    """The source's fingerprint, or None when the answer lacks the source's own content - a bot check or consent
    page served instead (no PDF, no <article> / <main> text, no amendment list): that is not a change."""
    if kind == "pdf":
        return {"sha256": hashlib.sha256(body).hexdigest(), "size": len(body)} if body.startswith(b"%PDF") else None
    if kind == "lex":  # lex.bg (windows-1251): one HistoryItem per entry, „Обн. ДВ. бр.133 …“ first, then „изм. ДВ. бр.98 …“;
        # its markup writes the class as class=\"HistoryItem\" (escaped quotes); an item ends at the </span> before „,“ / <br / </p
        s = body.decode("cp1251", "replace")
        items = re.findall(r'(?s)class=\\?"HistoryItem\\?"[^>]*>(.*?)</span>(?=\s*(?:,|<br|</p))', s)
        hist = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip() for x in items]
        return {"amendments": hist} if hist else None
    region = main_region(body.decode("utf-8", "replace"))
    text = strip_html(region) if region is not None else ""
    if not text:
        return None
    pdfs = sorted(set(html.unescape(h) for h in re.findall(r'(?i)href="([^"]+\.pdf[^"]*)"', region)))
    return {"text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "text_chars": len(text), "pdfs": pdfs}


def differences(kind, old, new):
    if kind == "pdf":
        return [] if old.get("sha256") == new["sha256"] else ["the PDF changed (%s -> %s bytes)" % (old.get("size"), new["size"])]
    if kind == "lex":
        o, n = old.get("amendments", []), new["amendments"]
        if o == n:
            return []
        added = [x for x in n if x not in o]
        return ["the amendment list changed" + (": new " + "; ".join(added) if added else " (%d -> %d entries)" % (len(o), len(n)))]
    out = []
    added = [p for p in new["pdfs"] if p not in old.get("pdfs", [])]
    gone = [p for p in old.get("pdfs", []) if p not in new["pdfs"]]
    if added:
        out.append("new PDF links: " + ", ".join(added))
    if gone:
        out.append("PDF links gone: " + ", ".join(gone))
    if old.get("text_sha256") != new["text_sha256"]:
        out.append("the main text changed (%s -> %s characters)" % (old.get("text_chars"), new["text_chars"]))
    return out


def load_source(key, url, fixtures):
    if not fixtures:
        return fetch(url)
    meta = json.load(open(os.path.join(fixtures, key + ".json"), encoding="utf-8"))
    path = os.path.join(fixtures, key + ".bin")
    return meta.get("status", 0), (open(path, "rb").read() if os.path.exists(path) else b""), meta.get("headers", {})


def main(argv):
    update = "--update" in argv
    fixtures = argv[argv.index("--fixtures") + 1] if "--fixtures" in argv else None
    path = argv[argv.index("--json") + 1] if "--json" in argv else os.path.join(HERE, "rules_sources.json")
    stored = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    fresh, changed, dead, unreachable, changed_src = {}, [], [], [], set()
    for key, kind, url, label in SOURCES:
        status, body, hdr = load_source(key, url, fixtures)
        if status in (404, 410):
            dead.append("%s - HTTP %s (the link is gone): %s" % (label, status, url))
            continue
        if status != 200 or not body:
            unreachable.append("%s - %s" % (label, ("HTTP %s" % status) if status else hdr.get("error", "no answer")))
            if key in stored:
                fresh[key] = stored[key]  # keep the last known fingerprint
            continue
        fp = fingerprint(kind, body)
        if fp is None:  # a bot check / consent page instead of the document: unknown, not changed
            unreachable.append("%s - the answer came without the document's own content (a bot check or consent page?)" % label)
            if key in stored:
                fresh[key] = stored[key]
            continue
        fp["url"] = url
        fresh[key] = fp
        if key not in stored:
            if not update:
                changed.append("%s - not checked before (run --update after a look)" % label)
                changed_src.add(key)
            continue
        for d in differences(kind, stored[key], fp):
            changed.append("%s - %s: %s" % (label, d, url))
            changed_src.add(key)
    for u in unreachable:
        print("::warning title=Rules source not reachable::" + u)
    if update:
        json.dump(fresh, open(path, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1, sort_keys=True)
        print("stored %d fingerprints in %s (%d sources did not answer: kept their old ones)" % (len(fresh), path, len(unreachable)))
        return 0
    for c in changed:
        print("CHANGED: " + c)
    for d in dead:
        print("DEAD LINK: " + d)
    ok = len(SOURCES) - len(changed_src) - len(dead) - len(unreachable)
    print("%d of %d sources unchanged, %d changed, %d dead links, %d not reachable" % (ok, len(SOURCES), len(changed_src), len(dead), len(unreachable)))
    if changed or dead:
        print("Re-check the changed text(s); update tools/rules_panel.py (its texts need the owner's „да“) and its date only after that; then run --update and commit tools/rules_sources.json.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
