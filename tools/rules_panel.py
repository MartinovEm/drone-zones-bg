"""The „Правила“ (Rules) pop-up: a short, unofficial summary of the drone rules in
Bulgaria, BG + EN, opened from the menu's «Инструменти» (ROADMAP A9). Every item ends
with links to the official texts; the wording was approved by the owner on 21.10.2026
and checked against those sources on RULES_DATE — change a word only with his approval
and move RULES_DATE only after a real re-check of the sources.

make_3d.py puts RULES_CSS into the style, RULES_HTML into the body and RULES_JS after
the shell script. Both languages are in the page; html[lang] (set by applyLang) shows one.
"""
import re
from html import escape

RULES_DATE = "21.10.2026"

_E947 = "https://eur-lex.europa.eu/legal-content/%s/TXT/?uri=CELEX:02019R0947-20250501"
_E945 = "https://eur-lex.europa.eu/legal-content/%s/TXT/?uri=CELEX:02019R0945-20250624"
_N6 = "https://www.caa.bg/sites/default/files/upload/documents/2026-01/%D0%9D%D0%A0_2023_664891.2025114.pdf"
_ZGV = "https://www.caa.bg/sites/default/files/upload/documents/2026-04/%D0%97%D0%93%D0%92%D1%8A%D0%B7%D0%B4_1972.2026032.pdf"
_DV87 = "https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=237772"      # ЗГВ чл. 62б, 63 + НК чл. 114е(2а)
_TARIFF = "https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=246145"    # ПМС № 164, ДВ бр. 91/2026
_EURO = "https://dv.parliament.bg/DVWeb/showMaterialDV.jsp?idMat=224950"      # Закон за въвеждане на еврото
_FORM = ("https://www.caa.bg/sites/default/files/uploads/%D0%97%D0%B0%D1%8F%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5"
         "%20%D0%91%D0%9B%D0%A1%20%D0%B7%D0%BE%D0%BD%D0%B8%20%D0%B8%20%D1%80%D0%B5%D0%B7%D0%B5%D1%80%D0%B2%D0%B8"
         "%D1%80%D0%B0%D0%BD%D0%B5%20%D0%BD%D0%B0%20%D0%92%D0%9F%2004.2026.pdf")
_CAA_REG = "https://www.caa.bg/bg/category/899/29604"
_CAA_KEP = "https://www.caa.bg/bg/category/899/29602"
_CAA_FAQ = "https://www.caa.bg/bg/category/899/29605"
_CAA_UAS = "https://www.caa.bg/bg/category/633"
_UAS = "https://uas.caa.bg"
_OPINION = "https://www.easa.europa.eu/en/document-library/opinions/opinion-no-062026"
_FAQ = "https://www.easa.europa.eu/en/faq/%s"
_KRS = "https://crc.bg/bg/statii/2587/pravila-za-svobodno-izpolzvane-na-radiochestotniq-spektar"
_KRS2 = "https://crc.bg/bg/statii/2480/prilojenie-2-ustroystva-s-malak-obseg-na-deystvie"
_CEPT = "https://docdb.cept.org/download/4980"
_HAM = "https://crc.bg/files/2025%20%D0%9F%D0%A0%D0%90%D0%92%D0%9D%D0%90/Pravila_radiolubiteli.pdf"
_ZZT = "https://www.lex.bg/laws/ldoc/2134445060"

# Each item: (title, subtitle or "", bullets, [(link label, url), ...]).
RULES = {
 "bg": {
  "title": "Правила за полети с дрон",
  "note": "Кратко неофициално резюме. Важи само официалният текст – връзките водят към него. "
          "Сверено с официалните текстове на " + RULES_DATE + ".",
  "src": "Източник",
  "items": [
   ("1. Регистрация на оператор", "", [
     "Регистрацията в ГД ГВА е задължителна, ако дронът е 250 г или повече, или има камера (или друг сензор за лични данни) и не е играчка. В „специфична“ категория – винаги.",
     "Регистрацията, обучението и изпитите са в uas.caa.bg. Нужен е КЕП (ГД ГВА посочва и безплатен мобилен КЕП).",
     "Такса за регистрация: 10,23 € (за развлечение) или 20,45 € (професионална дейност).",
     "Номерът на оператора се поставя на всеки дрон. Ако пилотът е под 18 г., се регистрира родител или попечител.",
     "Предстои (още не е закон): EASA предлага прагът да падне на 100 г."],
    [("Регламент 2019/947, чл. 14", _E947 % "BG" + "#art_14"), ("Наредба № Н-6", _N6),
     ("ГД ГВА: кога се изисква регистрация", _CAA_REG), ("ГД ГВА: КЕП", _CAA_KEP),
     ("Тарифа, ДВ бр. 91/2026", _TARIFF), ("uas.caa.bg", _UAS), ("EASA: предложение 06/2026", _OPINION)]),
   ("2. Свидетелство за правоспособност на дистанционно управляващ пилот", "", [
     "A1/A3: онлайн обучение и онлайн изпит – 40 въпроса, нужни са 75 %. Такса за изпита: 10,23 €.",
     "A2: след A1/A3 – самостоятелна практика, декларация и допълнителен изпит (поне 30 въпроса, 75 %). Такса: 20,45 €.",
     "Свидетелството важи 5 години и се носи при полет (не е нужно за дрон C0 или дрон под 250 г без клас).",
     "Минимална възраст: 16 г. Без минимум – за дрон-играчка клас C0, за самоделен дрон под 250 г и при полет под прекия надзор на дистанционно управляващ пилот със свидетелство."],
    [("Регламент 2019/947, чл. 9", _E947 % "BG" + "#art_9"), ("Регламент 2019/947, приложение", _E947 % "BG" + "#anx_1"),
     ("Наредба № Н-6", _N6), ("Тарифа, ДВ бр. 91/2026", _TARIFF)]),
   ("3. Основни правила („неограничена“ категория)", "", [
     "Дронът е под 25 кг.",
     "Полетът е винаги в пряка видимост.",
     "Височина – до 120 м от най-близката точка на земята.",
     "Без полети над групи хора.",
     "Без опасни товари и без пускане на предмети.",
     "Нощем на дрона свети зелена мигаща светлина.",
     "Без полети близо до или в зона на спасителна операция, освен с разрешение."],
    [("Регламент 2019/947, чл. 4", _E947 % "BG" + "#art_4"), ("Регламент 2019/947, приложение", _E947 % "BG" + "#anx_1")]),
   ("4. Подкатегории A1, A2, A3", "", [
     "A1: дронове под 250 г и C1. Дрон под 250 г може да прелита над отделни хора, но никога над групи. C1 не прелита над хора.",
     "A2: дрон C2, на поне 30 м от неучастващи хора (5 м в режим на ниска скорост).",
     "A3: C2, C3, C4, самоделни и стари дронове под 25 кг – далеч от хора и на поне 150 м от жилищни, търговски, промишлени и развлекателни зони."],
    [("Регламент 2019/947, приложение", _E947 % "BG" + "#anx_1")]),
   ("5. Класове, самоделни и стари дронове", "", [
     "C0–C4 са за „неограничена“ категория; C5 и C6 – за стандартните сценарии („специфична“ категория).",
     "Дрон без клас, пуснат на пазара преди 01.01.2024: под 250 г – A1; под 25 кг – A3.",
     "Самоделен (частно сглобен) дрон: под 250 г и под 19 m/s – A1; под 25 кг – A3."],
    [("Регламент 2019/947, чл. 20", _E947 % "BG" + "#art_20"), ("Регламент 2019/945", _E945 % "BG")]),
   ("6. FPV (с очила)", "", [
     "В „неограничена“ категория дронът трябва да е в пряка видимост. Полет с FPV очила е възможен само с наблюдател до пилота, който гледа дрона (позиция на EASA).",
     "Състезанията със зрители не са в „неограничена“ категория – нужно е разрешение."],
    [("EASA: полет с очила", _FAQ % "116511"), ("EASA: FPV", _FAQ % "140037"), ("EASA: състезания", _FAQ % "116510")]),
   ("7. Remote ID", "(дронът излъчва номера на оператора)", [
     "Задължително за класове C1, C2 и C3 – включено и с актуален номер на оператора.",
     "Не се изисква за C0, C4, самоделни и стари дронове."],
    [("Регламент 2019/947, приложение", _E947 % "BG" + "#anx_1"), ("EASA: задължения на оператора", _FAQ % "116467")]),
   ("8. Зони и разрешения", "", [
     "Всяка зона на ГД ГВА има свои условия. На картата: слоевете «Зони», «Активирани зони» и «NOTAM».",
     "Без разрешение не се лети в забранени и ограничени зони, в активирани зони и в охраняемите граници на летищата.",
     "При нарушение дронът може да бъде принуден да кацне; щетите са за сметка на нарушителя.",
     "Разрешение се иска от ГД ГВА със заявление. Въпроси: uas@caa.bg, 0897 013 264 и 02 937 1096 (вторник и четвъртък, 16:00–17:30)."],
    [("ЗГВ, чл. 62б (ДВ бр. 87/2025)", _DV87), ("Наредба № Н-6, чл. 55–57", _N6),
     ("Заявление (ГД ГВА)", _FORM), ("ГД ГВА: дронове", _CAA_UAS)]),
   ("9. Наказания", "", [
     "Полет без разрешение или в нарушение на правилата: глоба от 1 533,88 до 5 112,92 € (3 000–10 000 лв.).",
     "Застрашаване на самолет в полет: затвор от 3 до 10 години.",
     "Смущаване на авиационните радиосредства: глоба от 511,29 до 5 112,92 € (1 000–10 000 лв.)."],
    [("ЗГВ, чл. 143–144", _ZGV), ("Наказателен кодекс, чл. 114е (ДВ бр. 87/2025)", _DV87),
     ("Закон за въвеждане на еврото", _EURO)]),
   ("10. Застраховка", "", [
     "Задължителна за професионална дейност и за всеки дрон от 20 кг нагоре.",
     "За развлечение с дрон под 20 кг не е задължителна."],
    [("ЗГВ, чл. 19а", _ZGV), ("Наредба № Н-6, чл. 29 и 37", _N6), ("ГД ГВА: въпроси и отговори", _CAA_FAQ)]),
   ("11. Радио (видео и управление)", "", [
     "Без разрешително: 5,8 GHz – до 25 mW; 2,4 GHz – до 10 mW (100 mW за широколентови системи); 868 MHz – до 25 mW с ограничено време за предаване (869,4–869,65 MHz – до 500 mW, до 10 % от времето).",
     "915–919,4 MHz – само за устройства в мрежи за данни. 1,2 и 1,3 GHz не са свободни.",
     "Забранени са допълнителен усилвател и промяна на параметрите, зададени от производителя.",
     "С разрешително за радиолюбител (клас 1): 5650–5850 MHz до 5 W.",
     "Забранено е смущаването на авиационните радиосредства."],
    [("КРС: Правила за свободно използване", _KRS), ("КРС: Приложение 2", _KRS2), ("CEPT ERC/REC 70-03", _CEPT),
     ("КРС: Правила за радиолюбители", _HAM), ("ЗГВ, чл. 63 (ДВ бр. 87/2025)", _DV87)]),
   ("12. Природа", "", [
     "Законът за защитените територии няма изрична забрана за дронове.",
     "В резерватите е забранена всяка дейност, която законът не изброява като разрешена.",
     "За парковете важат заповедта за обявяване и планът за управление.",
     "На картата: слоевете «Натура 2000» и «Защитени територии»."],
    [("Закон за защитените територии (неофициален текст, lex.bg)", _ZZT)]),
   ("13. Преди полет (по EASA)", "", [
     "Свидетелство за съответната подкатегория.",
     "Актуална информация за зоните по пътя.",
     "Проверка за препятствия и хора наоколо.",
     "Изправни дрон и дистанционно; тегло в границите на подкатегорията.",
     "Номер на оператора на дрона и в Remote ID; актуални карти в дрона."],
    [("EASA: задължения на пилота", _FAQ % "116468"), ("EASA: задължения на оператора", _FAQ % "116467")]),
  ]},
 "en": {
  "title": "Drone flying rules",
  "note": "A short unofficial summary. Only the official text applies — the links lead to it "
          "(Bulgarian sources are in Bulgarian). Checked against the official texts on " + RULES_DATE + ".",
  "src": "Source",
  "items": [
   ("1. Operator registration", "", [
     "Registration with the Bulgarian CAA is required if the drone weighs 250 g or more, or has a camera (or another sensor that can capture personal data) and is not a toy. In the \"specific\" category — always.",
     "Registration, training and exams are done at uas.caa.bg. A qualified electronic signature is required (the CAA also points to a free mobile one).",
     "Registration fee: €10.23 (recreational) or €20.45 (professional activity).",
     "The operator number is displayed on every drone. If the pilot is under 18, a parent or guardian registers.",
     "Coming (not yet law): EASA proposes lowering the threshold to 100 g."],
    [("Regulation 2019/947, Art. 14", _E947 % "EN" + "#art_14"), ("Ordinance No N-6", _N6),
     ("CAA: when registration is required", _CAA_REG), ("CAA: electronic signature", _CAA_KEP),
     ("Fee tariff, State Gazette No 91/2026", _TARIFF), ("uas.caa.bg", _UAS), ("EASA: Opinion 06/2026", _OPINION)]),
   ("2. Remote pilot certificate", "", [
     "A1/A3: online training and an online exam of 40 questions; 75% is needed. Exam fee: €10.23.",
     "A2: after A1/A3 — self-practical training, a declaration and an additional exam (at least 30 questions, 75%). Fee: €20.45.",
     "The certificate is valid for 5 years and is carried during the flight (not needed for a C0 drone or a drone under 250 g without a class).",
     "Minimum age: 16. No minimum for a class C0 toy drone, a privately built drone under 250 g, or flying under the direct supervision of a certified remote pilot."],
    [("Regulation 2019/947, Art. 9", _E947 % "EN" + "#art_9"), ("Regulation 2019/947, Annex", _E947 % "EN" + "#anx_1"),
     ("Ordinance No N-6", _N6), ("Fee tariff, State Gazette No 91/2026", _TARIFF)]),
   ("3. Basic rules (\"open\" category)", "", [
     "The drone weighs under 25 kg.",
     "Always within visual line of sight.",
     "Up to 120 m from the closest point of the ground.",
     "No flying over assemblies of people.",
     "No dangerous goods and no dropping of objects.",
     "At night, a green flashing light is on.",
     "No flying close to or inside an emergency response area without permission."],
    [("Regulation 2019/947, Art. 4", _E947 % "EN" + "#art_4"), ("Regulation 2019/947, Annex", _E947 % "EN" + "#anx_1")]),
   ("4. Subcategories A1, A2, A3", "", [
     "A1: drones under 250 g and C1. A drone under 250 g may fly over individual people, but never over assemblies. C1 does not fly over people.",
     "A2: a C2 drone, at least 30 m from people not involved in the flight (5 m in low-speed mode).",
     "A3: C2, C3, C4, privately built and legacy drones under 25 kg — far from people and at least 150 m from residential, commercial, industrial or recreational areas."],
    [("Regulation 2019/947, Annex", _E947 % "EN" + "#anx_1")]),
   ("5. Classes, privately built and legacy drones", "", [
     "C0–C4 are for the \"open\" category; C5 and C6 for the standard scenarios (\"specific\" category).",
     "A drone without a class placed on the market before 1 January 2024: under 250 g — A1; under 25 kg — A3.",
     "A privately built drone: under 250 g and under 19 m/s — A1; under 25 kg — A3."],
    [("Regulation 2019/947, Art. 20", _E947 % "EN" + "#art_20"), ("Regulation 2019/945", _E945 % "EN")]),
   ("6. FPV (goggles)", "", [
     "In the \"open\" category the drone must be within visual line of sight. Flying with FPV goggles is possible only with an observer next to the pilot who watches the drone (EASA's position).",
     "Races with spectators are not in the \"open\" category — an authorisation is needed."],
    [("EASA: flying with goggles", _FAQ % "116511"), ("EASA: FPV", _FAQ % "140037"), ("EASA: races", _FAQ % "116510")]),
   ("7. Remote ID", "(the drone broadcasts the operator number)", [
     "Required for classes C1, C2 and C3 — switched on and with the current operator number.",
     "Not required for C0, C4, privately built and legacy drones."],
    [("Regulation 2019/947, Annex", _E947 % "EN" + "#anx_1"), ("EASA: operator duties", _FAQ % "116467")]),
   ("8. Zones and permissions", "", [
     "Each CAA zone has its own conditions. On the map: the «Zones», «Activated zones» and «NOTAM» layers.",
     "No flying without permission in prohibited and restricted zones, in activated zones and inside the guarded boundaries of airports.",
     "In case of a violation the drone may be forced to land; the damage is borne by the violator.",
     "Permission is requested from the CAA with an application. Questions: uas@caa.bg, +359 897 013 264 and +359 2 937 1096 (Tuesday and Thursday, 16:00–17:30)."],
    [("Civil Aviation Act, Art. 62b (State Gazette No 87/2025)", _DV87), ("Ordinance No N-6, Art. 55–57", _N6),
     ("Application form (CAA)", _FORM), ("CAA: drones", _CAA_UAS)]),
   ("9. Penalties", "", [
     "Flying without permission or in breach of the rules: a fine of €1,533.88 to €5,112.92 (BGN 3,000–10,000).",
     "Endangering an aircraft in flight: 3 to 10 years in prison.",
     "Interfering with aviation radio systems: a fine of €511.29 to €5,112.92 (BGN 1,000–10,000)."],
    [("Civil Aviation Act, Art. 143–144", _ZGV), ("Criminal Code, Art. 114e (State Gazette No 87/2025)", _DV87),
     ("Act on the Introduction of the Euro", _EURO)]),
   ("10. Insurance", "", [
     "Required for professional activity and for every drone of 20 kg or more.",
     "Not required for recreational flying with a drone under 20 kg."],
    [("Civil Aviation Act, Art. 19a", _ZGV), ("Ordinance No N-6, Art. 29 and 37", _N6), ("CAA: questions and answers", _CAA_FAQ)]),
   ("11. Radio (video and control)", "", [
     "Without a licence: 5.8 GHz — up to 25 mW; 2.4 GHz — up to 10 mW (100 mW for wideband systems); 868 MHz — up to 25 mW with a limited transmit time (869.4–869.65 MHz — up to 500 mW, at most 10% of the time).",
     "915–919.4 MHz is only for devices in data networks. 1.2 and 1.3 GHz are not free to use.",
     "Extra amplifiers and changing the parameters set by the manufacturer are prohibited.",
     "With a radio amateur licence (class 1): 5650–5850 MHz up to 5 W.",
     "Interfering with aviation radio systems is prohibited."],
    [("CRC: rules for free use of the radio spectrum", _KRS), ("CRC: Annex 2", _KRS2), ("CEPT ERC/REC 70-03", _CEPT),
     ("CRC: radio amateur rules", _HAM), ("Civil Aviation Act, Art. 63 (State Gazette No 87/2025)", _DV87)]),
   ("12. Nature", "", [
     "The Protected Areas Act has no explicit drone ban.",
     "In reserves every activity not listed as allowed by the law is prohibited.",
     "For parks, the designation order and the management plan apply.",
     "On the map: the «Natura 2000» and «Protected areas» layers."],
    [("Protected Areas Act (unofficial text, lex.bg)", _ZZT)]),
   ("13. Before the flight (per EASA)", "", [
     "A certificate for the relevant subcategory.",
     "Up-to-date information on the zones along the route.",
     "A check for obstacles and people around.",
     "A working drone and remote control; a weight within the subcategory limits.",
     "The operator number on the drone and in Remote ID; up-to-date maps in the drone."],
    [("EASA: remote pilot duties", _FAQ % "116468"), ("EASA: operator duties", _FAQ % "116467")]),
  ]},
}

# keep a number with its unit / its thousands on one line (a no-break space; the words are unchanged)
_UNITS = r"(?:г|кг|м|лв|W|mW|GHz|MHz|m/s|g|kg|m|години|years)\b"
def _nb(s):
    s = re.sub(r"(?<=\d) (?=\d{3}\b)", " ", s)
    s = re.sub(r"(?<=\d) (?=[€%])", " ", s)
    return re.sub(r"(?<=\d) (?=" + _UNITS + ")", " ", s)

def _block(lang):
    L = RULES[lang]
    h = ['<div class="rl-%s"><p class="rlnote">%s</p>' % (lang, escape(L["note"], quote=False))]
    for title, sub, bullets, links in L["items"]:
        h.append('<details><summary>%s%s</summary><ul>%s</ul><p class="rlsrc">%s: %s</p></details>' % (
            escape(title, quote=False), (' <span class="rlsub">%s</span>' % escape(sub, quote=False)) if sub else "",
            "".join("<li>%s</li>" % escape(_nb(b), quote=False) for b in bullets), L["src"],
            " · ".join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (escape(u), escape(t, quote=False)) for t, u in links)))
    h.append("</div>")
    return "".join(h)

RULES_HTML = ('<div id="rules" hidden role="dialog" aria-modal="true" aria-labelledby="rulesh"><div class="rlbox">'
  '<div class="rlhead"><h2 id="rulesh"><span class="rl-bg">%s</span><span class="rl-en">%s</span></h2>'
  '<button class="pclose" id="rulesclose" type="button" aria-label="close">✕</button></div>'
  '<div class="rlbody">%s%s</div></div></div>') % (escape(RULES["bg"]["title"]), escape(RULES["en"]["title"]), _block("bg"), _block("en"))

RULES_CSS = r"""
/* ---- the „Правила“ pop-up (ROADMAP A9): over the map; phones (narrow OR short) = the whole screen ---- */
#rules{position:fixed;top:0;right:0;left:0;bottom:var(--vp-bottom,0px);z-index:3000;display:flex;align-items:center;justify-content:center;
 padding:16px;box-sizing:border-box;background:rgba(0,0,0,.35);font:14px/1.45 system-ui,'Segoe UI',Roboto,sans-serif;color:var(--fg)}
#rules[hidden]{display:none}
#rules .rlbox{width:min(720px,100%);max-height:100%;display:flex;flex-direction:column;box-sizing:border-box;background:var(--glass-strong);
 -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border:1px solid var(--border);border-radius:14px;
 box-shadow:0 6px 28px rgba(0,0,0,.35);overflow:hidden}
#rules .rlhead{display:flex;align-items:center;gap:8px;padding:10px 10px 8px 16px;border-bottom:1px solid var(--border)}
#rules h2{margin:0;flex:1;font-size:17px;font-weight:700}
#rules .rlbody{overflow:auto;padding:6px 16px 14px;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}
#rules .rlnote{margin:6px 0 8px;font-size:12px;font-style:italic;color:var(--muted)}
#rules details{border-top:1px solid var(--border)}
#rules summary{cursor:pointer;padding:9px 2px;font-weight:600}
#rules summary::marker{color:var(--muted)}
#rules .rlsub{font-weight:400;color:var(--muted)}
#rules ul{margin:0 0 4px;padding-left:20px}
#rules li{margin:3px 0}
#rules .rlsrc{margin:6px 0 12px;font-size:12px;color:var(--muted)}
#rules a{color:var(--accent);text-decoration:none}
#rules a:hover{text-decoration:underline}
html[lang="en"] #rules .rl-bg,html:not([lang="en"]) #rules .rl-en{display:none}
@media (max-width:640px), (max-height:500px){
 #rules{padding:0}
 #rules .rlbox{width:100%;height:100%;border:0;border-radius:0}
}
"""

RULES_JS = r"""
// ---- the „Правила“ pop-up (ROADMAP A9): opened from the menu's «Инструменти»; the menu and any other
// card close; ✕, ESC or a click outside the box closes it. Not part of a shared view. ----
(function(){
  var rl = document.getElementById('rules'), btn = document.getElementById('rulesbtn'), x = document.getElementById('rulesclose');
  if (!rl || !btn || !x) return;
  function open(){
    if (window.closePanel) window.closePanel();
    if (window.closeWxPanel) window.closeWxPanel();
    if (window.closeBmPanel) window.closeBmPanel();
    if (window.collapseLoupe) window.collapseLoupe();
    rl.hidden = false; x.focus(); }
  function close(){ rl.hidden = true; }
  btn.onclick = function(e){ e.stopPropagation(); open(); };
  x.onclick = function(e){ e.stopPropagation(); close(); };
  rl.addEventListener('click', function(e){ e.stopPropagation(); if (e.target === rl) close(); });
  // capture phase: ESC closes only the pop-up (not the search or the ruler underneath)
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && !rl.hidden){ e.stopPropagation(); close(); } }, true);
})();
"""
