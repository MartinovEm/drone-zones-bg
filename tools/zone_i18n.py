"""English renderings of the finite set of official CAA zone texts, for display on the
EN toggle. The Bulgarian source (from the CAA JSON) stays the authority; this is an
unofficial convenience translation, keyed by the exact Bulgarian string (trimmed).
Only the distinct templates that appear in the data are listed; anything not found
falls back to the original Bulgarian text."""

def has_cyr(s):
    """True if the string contains any Cyrillic letter."""
    return any(0x0400 <= ord(ch) <= 0x04FF for ch in (s or ""))


# Free / personal e-mail providers. When a zone's official contact e-mail is one of
# these, it is an individual's personal address (the CAA sometimes lists such), so the
# map hides the e-mail and phone and shows only the authority name. Official-domain
# contacts (e.g. uas@caa.bg) are kept. The source JSON is never edited.
FREEMAIL = {
    "gmail.com", "googlemail.com", "abv.bg", "mail.bg", "dir.bg", "gbg.bg",
    "yahoo.com", "yahoo.co.uk", "hotmail.com", "outlook.com", "live.com",
    "icloud.com", "me.com", "gmx.com", "gmx.net", "protonmail.com", "proton.me",
    "mail.ru", "aol.com", "zoho.com",
}


# zone "message" (official description) -> English
MSG_EN = {
    "Полети в тази зона могат да се изпълняват само след разрешение от ГД ГВА. Минимален интервал от време за подаване на заявление е 5 работни дни преди планираната дата.":
        "Flights in this zone are allowed only after authorisation from the Bulgarian CAA. Applications must be submitted at least 5 working days before the planned date.",
    "Полети в тази зона могат да се изпълняват само след разрешение от ГД ГВА. Минимален интервал от време за подаване на заявление е 7 работни дни преди планираната дата.":
        "Flights in this zone are allowed only after authorisation from the Bulgarian CAA. Applications must be submitted at least 7 working days before the planned date.",
    "Полети в тази зона над 50м могат да се изпълняват само след разрешение от ГД ГВА. Минимален интервал от време за подаване на заявление е 7 работни дни преди планираната дата.":
        "Flights in this zone above 50 m are allowed only after authorisation from the Bulgarian CAA. Applications must be submitted at least 7 working days before the planned date.",
    "Полети в тази зона могат да се изпълняват само след разрешение от ГД ГВА. Минимален интервал от време за подаване на заявление е 1 месец преди планираната дата.":
        "Flights in this zone are allowed only after authorisation from the Bulgarian CAA. Applications must be submitted at least 1 month before the planned date.",
    "Полети в тази зона могат да се изпълнят само след специално разрешение на ГД ГВА. Минималният интервал от време, необходим между заявката за разрешение и започването на работа в зоната е 3 раб. дни.":
        "Flights in this zone are allowed only after special authorisation from the Bulgarian CAA. The minimum time between the authorisation request and the start of activity in the zone is 3 working days.",
    "Полети в тази зона могат да се изпълнят само след специално разрешение на ГД ГВА. Минималният интервал от време, необходим между заявката за разрешение и започването на работа в зоната е 7 раб. дни.":
        "Flights in this zone are allowed only after special authorisation from the Bulgarian CAA. The minimum time between the authorisation request and the start of activity in the zone is 7 working days.",
    "Полети в тази зона могат да се изпълнят само след разрешение на ГД ГВА. Минималният интервал от време, необходим между заявката за разрешение и започването на работа в зоната е 7 дни.":
        "Flights in this zone are allowed only after authorisation from the Bulgarian CAA. The minimum time between the authorisation request and the start of activity in the zone is 7 days.",
    "Операторът на БЛС изисква предварително разрешение за полет чрез подаване на заявление в ГД ГВА.":
        "The UAS operator must obtain prior flight authorisation by submitting an application to the Bulgarian CAA.",
    "Забраняват се полетите с безпилотни летателни системи в установената зона.":
        "Flights of unmanned aircraft systems (UAS) are prohibited in this zone.",
    "Забраняват се полетите с безпилотни летателни системи в установената зона, освен с тези на заявителя.":
        "Flights of unmanned aircraft systems (UAS) are prohibited in this zone, except those of the applicant.",
    "Забраняват се полети с БЛС, изисква се предварително разрешение за полет от заявителя. Полетът в зоната се извършва под условия.":
        "UAS flights are prohibited; prior flight authorisation from the applicant is required. Flights in the zone are subject to conditions.",
    "Зона за сигурност забранена за полети на БЛС от земната повърхност до височина 120 метра":
        "Security zone; UAS flights prohibited from ground level up to 120 metres.",
    "Зона, забранена за полети на БЛС от земната повърхност до височина 120 метра":
        "Zone prohibited for UAS flights from ground level up to 120 metres.",
    "Да се уведомява лицето за контакт за планираната дейност 10 дни предварително":
        "Notify the contact person of the planned activity 10 days in advance.",
    "Да се уведомява лицето за контакт за планираната дейност 15 дни предварително":
        "Notify the contact person of the planned activity 15 days in advance.",
    "Да се уведомява лицето за контакт за планираната дейност 20 дни предварително":
        "Notify the contact person of the planned activity 20 days in advance.",
    "Да се уведомява лицето за контакт за планираната дейност 45 дни предварително":
        "Notify the contact person of the planned activity 45 days in advance.",
}

# restrictionConditions text -> English
COND_EN = {
    "Да се уведоми заявителят за планираната дейност.":
        "Notify the applicant of the planned activity.",
}

# zoneAuthority name -> English (only the clear, dominant one; others stay as-is)
AUTH_EN = {
    "ГД ГВА": "Bulgarian CAA",
    "ВВС": "Air Force",
    "ВМС": "Navy",
    "СВ.": "Land Forces",
    "СВ..": "Land Forces",
    "НВУ": "National Military University",
    "ВА.": "Military Academy",
    "Национална гвардейска част": "National Guard unit",
}

# otherReasonInfo ("Details") -> English, keyed by whitespace-normalised Bulgarian.
# Only descriptive phrases are translated; Latin codes (TRA33, D224...) are kept as-is by
# the builder, and Cyrillic proper names not listed here are hidden in EN mode.
OI_EN = {
    "Министерство на правосъдието": "Ministry of Justice",
    "Да се уведоми заявителят за планираната дейност.": "Notify the applicant of the planned activity.",
    "Стратегически обект от значение за националната сигурност, определен с ПМС №181/2009 г.":
        "Strategic site of national-security importance, designated by Council of Ministers Decree No. 181/2009.",
    'Яз. "Бели Искър" е Стратегически обект, съгласно постановление на Министерски Съвет № 181/20.07.2009 г. Вододайна зона.':
        "Beli Iskar reservoir: strategic site per Council of Ministers Decree No. 181/20.07.2009. Water-supply zone.",
    'СПСОВ "Кубратово" е критично инфраструктурно звено за София.':
        "Kubratovo wastewater treatment plant: critical infrastructure for Sofia.",
    'Пречиствателна станция за питейни води "Бистрица"':
        "Bistritsa drinking-water treatment plant.",
    'Пречиствателна станция за питейни води "Панчарево" е част от критичната инфраструктура на ВиК системата.':
        "Pancharevo drinking-water treatment plant: part of the water-utility critical infrastructure.",
    "Централно управление Булгартрансгаз ЕАД": "Bulgartransgaz EAD headquarters.",
    "Зона H010-B Зоната е активна от 01 октомври до 30 април.": "Zone H010-B; active 1 October – 30 April.",
    "Зона H010-B Зоната е активна от 01 май до 30 септември.": "Zone H010-B; active 1 May – 30 September.",
    "активна от о1 април до 30октомври": "active 1 April – 30 October.",
    "Зони - Районна диспечерска служба /РДС/ и сървърно помещение /СП/ в РЗ СЗЕР Ботевград":
        "Zones: regional dispatch service and server room, Botevgrad.",
    "Зони - Районна диспечерска служба /РДС/ и сървърно помещение /СП/ в РЗ ЮИЕР Стара Загора":
        "Zones: regional dispatch service and server room, Stara Zagora.",
}

# Auto-translation cache (machine translations of any Bulgarian text not curated above),
# filled and kept fresh by tools/build.py at build time. Curated entries always win.
import json as _json, os as _os
try:
    AUTO = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                         "zone_i18n_auto.json"), encoding="utf-8"))
except Exception:
    AUTO = {}

_CURATED = {}
for _m in (MSG_EN, COND_EN, OI_EN):
    for _k, _v in _m.items():
        _CURATED[" ".join(_k.split())] = _v


def en_text(bg):
    """English for a Bulgarian zone text: curated first, then the cached auto-translation,
    then the original if it has no Cyrillic (a Latin code), else '' (hidden until a later
    build translates it). The Bulgarian source always stays authoritative and is what the
    BG view shows; the EN view never shows Bulgarian."""
    if not bg:
        return ""
    key = " ".join(bg.split())
    if key in _CURATED:
        return _CURATED[key]
    if key in AUTO:
        return AUTO[key]
    return "" if has_cyr(bg) else bg
