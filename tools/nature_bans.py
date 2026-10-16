"""Explicit drone / flight rules in Bulgaria's protected areas, for the „Природа“ layers.

Owner rule (16.10.2026): a protected area is marked red ONLY where an official document
explicitly bans drones or flying, and every entry carries the verbatim quote (Bulgarian) plus a
link to the document. Checked 15-16.10.2026: all 1077 territories of the ИАОС register, the
management plans of the 14 national and nature parks and 80 more plans, and the designation
orders of 338 of the 340 Natura 2000 sites (the MOEW does not post the orders of BG0000116
Камчия and BG0000610 Река Янтра). Re-check when the data is refreshed (about once a year).

Territories are keyed by (DesigAbbr, NameBg) exactly as the MOEW's open data names them;
Natura 2000 sites by their site code. make_natura.py stops if a key no longer matches.
- BANS: kind "full" = the whole territory (red outline); "part" = only a part of it or a part
  of the year (red dashed outline), "w" says where/when.
- Reserves and maintained reserves (BG01, BG04) are red by the law itself (RESERVE_LAW).
- HANG: bans on hang-gliding / paragliding only — drones are not named, so not red (owner 16.10):
  one line in the popup. NATURA_HANG: the same for Natura 2000 sites.
- NOTE: other rules that name aircraft (not a flight ban): one line in the popup.
"""

BANS = {
    ("BG02", "Пирин"): {
        "kind": "full",
        "q": "Не се разрешава летене под сто метра над земята с каквото и да е летателно средство (хеликоптери, "
             "делта планери, парапланери и др.) и кацане извън туристическата зона, определена от ПУ. Изключение се "
             "прави за спасителни операции и поддържащи дейности на Парка, които трябва да бъдат разрешени от ДНП.",
        "e": "Flying below 100 m above the ground with any aircraft, and landing outside the tourist zone, are not "
             "allowed (except rescue and park work).",
        "d": "План за управление на НП „Пирин“ (Решение на МС № 646/06.08.2004, ДВ, бр. 73/2004), раздел I, т. 1, подт. 10",
        "u": "https://pirinnationalpark.egov.bg/wps/wcm/connect/pirinnationalpark.egov.bg-26148/"
             "4e8e77f4-11b8-4f1a-8625-bf4fa8104532/Plan-za-uprav.pdf?MOD=AJPERES",
    },
    ("BG05", "Русенски Лом"): {
        "kind": "full",
        "q": "Забранява се използването на дронове, освен за служебни цели от ДПП Русенски Лом, РИОСВ Русе и ДЛС Дунав Русе.",
        "e": "Drones are banned, except for official use by the park, RIOSV Ruse and the state game estate.",
        "d": "План за управление на ПП „Русенски Лом“ (Решение на МС № 760/12.10.2022, ДВ, бр. 83/2022), т. 3.2.1.1, (21)",
        "u": "https://www.moew.government.bg/static/media/ups/tiny/filebase/Nature/Protected_areas/Planove_za_upravlenie/"
             "%D0%90%D0%9F%D0%A3-%D0%A0%D1%83%D1%81%D0%B5%D0%BD%D1%81%D0%BA%D0%B8%20%D0%9B%D0%BE%D0%BC-2022/"
             "Text-PU-2-%D0%9C%D0%A1-%D0%BE%D0%BA%D1%82-2022.pdf",
    },
    ("BG06", "Манастирска стълба"): {
        "kind": "full",
        "q": "Забранява се управление и снимане с летящи апарати (дронове и др.) освен за провеждане на проучвателни и контролни дейности.",
        "e": "Flying and filming with drones is banned, except for research and control.",
        "d": "Заповед № РД-124/09.02.2024 (ДВ, бр. 19/2024), т. 13",
        "u": "https://eea.government.bg/zpo/bg/area.jsp?NEM_Partition=1&categoryID=6&areaID=619",
    },
    ("BG06", "Пода"): {
        "kind": "full",
        "q": "…се забранява: … 13. Прелитането с каквито и да е летателни средства по-ниско от 2000 м над защитената местност",
        "e": "Overflight with any aircraft lower than 2000 m above the site is banned.",
        "d": "План за управление на ЗМ „Пода“ (Заповед № РД-919/08.10.2002, ДВ, бр. 108/2002)",
        "u": "https://www.moew.government.bg/static/media/ups/tiny/filebase/Nature/Protected_areas/Planove_za_upravlenie/"
             "Plan_za_uprawlenie_ZM_PODA-April_2002_1_.pdf",
    },
    ("BG04", "Сребърна"): {  # a maintained reserve: red by the law anyway; its plan also bans aircraft outright
        "kind": "full",
        "q": "Не се допуска използване на летателни средства във въздушното пространство над ПР, с изключение (при доказана "
             "необходимост) при научни изследвания.",
        "e": "No aircraft may be used in the airspace over the reserve, except for proven research needs.",
        "d": "План за управление на ПР „Сребърна“ (Заповед № РД-565/13.10.2016, ДВ, бр. 87/2016), т. 3.2.3.1, усл. 6",
        "u": "https://eea.government.bg/zpo/bg/area.jsp?NEM_Partition=1&categoryID=4&areaID=8",
    },
    ("BG05", "Врачански Балкан"): {
        "kind": "part",
        "w": "само в зоните „Котля“ и „Веждата“, февруари – август",
        "q": "зона „Котля“: Ниско прелитане и полети на планеристи през гнездовия сезон на птиците (м. февруари – август); "
             "зона „Веждата“: Ниско прелитане (под 200 м ) през гнездовия сезон на птиците (м. февруари-август)",
        "e": "Low flying is banned only in the zones Kotlya and Vezhdata, February to August (nesting season).",
        "d": "План за управление на ПП „Врачански Балкан“ (Решение на МС № 750/14.10.2011, ДВ, бр. 82/2011), зони 2.3 и 2.14",
        "u": "https://www.moew.government.bg/static/media/ups/tiny/filebase/Nature/Protected_areas/0_Sadarjanie.pdf",
    },
    ("BG06", "Дренето"): {
        "kind": "part",
        "w": "само до 100 м около колонията на сивите чапли и белите щъркели (зона А)",
        "q": "Забрана за ползване на дронове и Безпилотно летателно средство в радиус от 100 метра от границите на зона А и височина под 120 м.",
        "e": "Drones below 120 m are banned within 100 m of zone A (the grey heron and white stork colony).",
        "d": "План за управление на ЗМ „Дренето“ (Заповед № РД-241/10.04.2023, ДВ, бр. 36/2023)",
        "u": "https://eea.government.bg/zpo/bg/area.jsp?NEM_Partition=1&categoryID=6&areaID=51",
    },
}

# ЗЗТ чл. 17, ал. 1 „В резерватите се забраняват всякакви дейности, с изключение на: …“ and
# чл. 27, ал. 1 „В поддържаните резервати се забраняват всякакви дейности, с изключение на: …“
RESERVE_LAW = {"cats": ("BG01", "BG04"), "u": "https://lex.bg/laws/ldoc/2134445060"}

HANG = {
    ("BG06", "Патронка"): "Забранява се провеждане на мероприятия по алпинизъм и делтапланеризъм",
    ("BG06", "Момина скала"): "Забранява се алпинизма и делтапланеризма",
    ("BG06", "Орешари"): "Забранява се алпинизъм и делтапланеризъм",
    ("BG06", "Средна Арда"): "Забранява се алпинизъм и делтапланеризъм",
    ("BG06", "Юмрук скала"): "Забранява се алпинизъм и делтапланеризъм",
    ("BG06", "Големият сипей"): "Забранява се алпинизма и делтапланеризма",
    ("BG06", "Черната скала"): "Забранява се алпинизма и делтапланеризма",
    ("BG06", "Меандри на Бяла река"): "Забранява се алпинизма и делтапланеризма",
    ("BG06", "Огняново-Синитевски рид"): "Забранява се делта- и парапланеризмът",
    ("BG06", "Скален комплекс Караджов камък"): "Забранява се използването на скалния комплекс за скално катерене, алпинизъм, "
                                                "парапланеризъм, делтапланеризъм и мотоделтапланеризъм",
    ("BG06", "Рояшка скала"): "Забранява се скалното катерене, алпинизмът и планеризмът",
    ("BG06", "Голямо и малко було"): "Забранява се скално катерене, алпинизъм, парапланеризъм, делтапланеризъм и други дейности, "
                                     "водещи до безпокойство на гнездящите птици, през периода от 1 март до 31 август",
    ("BG06", "Мадарски скални венци"): "Забранява се практикуване на парапланеризъм и делтапланеризъм",
    ("BG06", "Козница"): "Забранява се скалното катерене, алпинизъм, парапланеризъм, делтапланеризъм и мотоделтапланеризъм",
    ("BG03", 'Скален масив "Белинташ"'): "Забранява се скално катерене, алпинизъм, парапланеризъм, делтапланеризъм и мото-делтапланеризъм",
}

NOTE = {
    ("BG05", "Рилски манастир"): {
        "q": "Безпокоене (включително чрез използване на летателни средства), убиване, улавяне, преследване и нараняване на диви животни",
        "e": "Disturbing wild animals, including by aircraft, is banned.",
        "d": "План за управление на ПП „Рилски манастир“ (Решение на МС № 121/12.03.2010, ДВ, бр. 23/2010), т. 1.1.2, т. 5",
        "u": "https://www.moew.government.bg/static/media/ups/tiny/filebase/Nature/Protected_areas/Planove_za_upravlenie/Rila_Monastery_Bul.pdf",
    },
}

_N2K = "https://natura2000.egov.bg/EsriBg.Natura.Public.Web.App/PublicDownloads/Auto/PS_SPA/%s/%s_PS_11.pdf"
NATURA_HANG = {
    "BG0002014": {"q": "скалното катерене, делта- и парапланеризмът в периода на гнездене от 1 март до 31 юли",
                  "d": "Заповед № РД-787/29.10.2008 (ДВ, бр. 105/2008), т. 6.5", "u": _N2K % ("BG0002014", "BG0002014")},
    "BG0002048": {"q": "практикуването на делта- и парапланеризъм",
                  "d": "Заповед № РД-853/15.11.2007 (ДВ, бр. 100/2007), т. 7.8", "u": _N2K % ("BG0002048", "BG0002048")},
    "BG0002102": {"q": "скалното катерене и практикуването на делта- и парапланеризъм през периода на гнездене от 1 март до 31 юли",
                  "d": "Заповед № РД-576/08.09.2008 (ДВ, бр. 85/2008), т. 6.8", "u": _N2K % ("BG0002102", "BG0002102")},
}

# The MOEW's SiteCode is the ИАОС register's areaID (1063 of 1067 checked on 16.10.2026), with
# these exceptions: two pairs share a code, and two sites are not in the register under it.
REGISTER_FIX = {
    ("BG06", "Манастирска стълба"): "6/619",          # 6/620 is „Язовир Мрамор“
    ("BG01", "Вельов вир (Водните лилии)"): "4/22",  # a maintained reserve in the register; 1/22 is „Мантарица“
    ("BG03", "Еленска глава"): "",                    # not in the register under its code -> the register's front page
    ("BG06", "Залив Корал"): "",
}
