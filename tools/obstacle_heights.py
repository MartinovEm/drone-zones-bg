"""Typical heights and minimum wire heights for the obstacles layer (make_obstacles.py).

OpenStreetMap rarely carries a height (power towers 2 of 59,794; poles 11 of 59,403; wind
turbines 6 of 484 in Bulgaria, 17.10.2026), so an obstacle without one gets a TYPICAL height by
type / voltage, which the map labels „типична“ (owner 17.10.2026). Every value comes from a
real source, quoted here (all checked 17.10.2026). No Bulgarian source gives the TOTAL height of
a transmission tower — ESO publishes only the height of the lowest conductor — so the towers'
totals come from the German DGUV guide. Masts, towers and chimneys get no typical height (they
range from about 20 to 300 m): only their own OSM height, if any.
"""

DGUV = "https://publikationen.dguv.de/widgets/pdf/download/article/878"

# Transmission towers, by the highest voltage of the lines on them (kV class -> metres).
# "low" = the height of the lowest conductor at the tower, from ESO's own documents.
TOWERS = {
    400: {"h": 40, "range": "35–75", "low": 24.5,
          "src": "DGUV BGI/GUV-I 8677-2 (2012): „ca. 35 – 75 m“ (220 and 380 kV); ESO, 400 kV Марица изток – "
                 "Бургас, spec. 1.4: „с базова височина за нормалния стълб 24,5 метра“; Наредба № 3, табл. 49: "
                 "„… се приема височината на по-високия стълб, но не по-малко от 40 m“",
          "u": DGUV},
    220: {"h": 35, "range": "35–75", "low": 22,
          "src": "DGUV (as above); ESO, 220 kV Дразки: lowest conductor 22 m (type НТ), 21 m (ЪТ)",
          "u": "https://www.eso.bg/fileObj.php?oid=5307"},
    110: {"h": 27.5, "range": "25–30", "low": 16,
          "src": "DGUV: „Masthöhe ca. 25 – 30 m“ (110 kV); ESO, 110 kV Вардим: „активна височина за нормалния "
                 "стълб 16 метра“",
          "u": DGUV},
}

# Distribution poles: height above the ground = pole length minus the depth in the ground.
POLES = {
    20: {"h": 11,
         "src": "Електроразпределителни мрежи Запад, standard 20 02 1201 (in force 15.07.2026): 13 m pole, "
                "„Дълбочина на вкопаване 1800 mm“",
         "u": "https://ermzapad.bg/documents/18498/20_02_1201_-_%D0%A1%D1%82%D0%BE%D0%BC%D0%B0%D0%BD%D0%BE%D0%B1%D0%B5%D1%82%D0%BEe%D0%BD_%D1%81%D1%82%D1%8A%D0%BB%D0%B1_%D1%86%D0%B5%D0%BD%D1%82%D1%80%D0%BE%D1%84%D1%83%D0%B3%D0%B0%D0%BB%D0%B5%D0%BD_-_13_m_%D0%B7%D0%B0_%D0%92%D0%9B_20_kV_6ZAOEk7.pdf"},
    0.4: {"h": 8,
          "src": "Електрохолд, standard 20 02 140z (in force 12.09.2024): 9.5 m pole, „Дълбочина на вкопаване 1600 mm“",
          "u": "https://electrohold.bg/documents/4819/20_02_140z_-centrofugalen_95_m_zblLEEO.pdf"},
}
POLE_UNKNOWN = 11   # owner 17.10.2026: a pole whose line has no voltage in OSM gets the 20 kV pole (the taller)

# Substation portals (power=portal): the steel frames where a line ends in a substation's open
# switchyard (ESO: „Порталите представляват П-образни конструкции, изпълнени от стоманорешетъчни
# колони и ригели“), by the voltage of the line on them. "beam" = the height of the cross-beam the
# wires hang from, "h" = the top (the columns' peaks above the beam, where a figure exists), "w" = one
# bay (the span between two legs), "rods" = the top of the lightning rod / mast that SOME portals carry.
# 110 and 400 kV from ESO's own documents (checked 18.10.2026). No Bulgarian figure for 220 kV, so a
# Soviet type design is used (foreign); ESO's range for the line portals of all classes is 10-25 m high
# and 9-22 m wide, so a 220 kV portal is drawn with the narrowest bay. A portal of unknown voltage takes
# the 110 kV one; a 20 kV portal gets none (owner 18.10.2026).
PORTALS = {
    400: {"h": 25, "beam": 25, "w": 22,
          "src": "ESO, ЦУ/2017/088 (п/ст Бургас, п/ст Варна-750): „изводните и помощните портали са с височина "
                 "25 m“; ЦУ/2018/122 (п/ст Столник): ригелите на изводните портали са с „дължина 22 000mm (осово "
                 "между колоните)“",
          "u": "https://webapps.eso.bg/zop_profile/page3download.php?id=52927&faID=70926&fn=1&fname=%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D0%B0%D1%86%D0%B8%D1%8F.pdf"},
    220: {"h": 17, "beam": 17, "w": 9, "foreign": True,
          "src": "no Bulgarian figure; Soviet type design 3.407.9-149 (portals ПС-220Я / Ш): „Высота, м: 17 (17,2)“; "
                 "ESO's range for line portals (framework specification 2018): „височина: 10,00 m ÷ 25,00 m и "
                 "широчина: 9,00 m ÷ 22,00 m“",
          "u": "https://aldeks.ru/portalyi_oru/220_kv/"},
    110: {"h": 12.5, "beam": 10, "w": 9, "rods": 16.5,
          "src": "ESO, п/ст Габрово (2018): „стоманорешетъчна рамка с височина 10.00 м и два отвора 9.00 м“, „връх на "
                 "колоната с височина 2500 мм“, „мълниеприемна мачта с дължина 4.00 м“; п/ст Търговище Индустрия "
                 "(2025): „с височина до точката на окачване на проводниците h=10 m (изводни портали)“",
          "u": "https://webapps.eso.bg/zop_profile/page3download.php?id=64513&faID=84649&fn=1&fname=%D0%9F%D1%80.1+-+%D0%A2%D0%B5%D1%85%D0%BD%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8+%D1%81%D0%BF%D0%B5%D1%86%D0%B8%D1%84%D0%B8%D0%BA%D0%B0%D1%86%D0%B8.pdf"},
}

LIFT_PYLON = {"h": 15, "range": "5–23",
              "src": "two lift projects in France (MRAe Occitanie 2024APO137, a chair lift: „8 pylônes d'une hauteur "
                     "de 5 à 23 mètres“; 2024APO77, a gondola: 6.5–23 m) — no Bulgarian figures found",
              "u": "https://www.mrae.developpement-durable.gouv.fr/IMG/pdf/2024apo137.pdf"}

# Wind turbines: the height to the blade tip (hub + rotor / 2). The turbines of the four farms
# below are listed by their OSM node ids, as matched in the research of 17.10.2026 (e.g. Свети
# Никола: all 52 turbine coordinates of the AES report have an OSM node within 46 m; a box around
# a farm would also catch its neighbours' turbines); any other turbine takes WIND (the median of
# these 123). A turbine re-mapped in OSM under a new id falls back to WIND - make_obstacles.py
# says how many listed ids it still finds.
WIND = {"h": 125, "range": "100–150", "src": "the median of the 123 turbines of the four farms below", "u": ""}
WIND_FARMS = [
    {"key": "stnikola", "n": "Свети Никола", "m": "Vestas V90-3.0", "h": 150,
     "src": "AES: „52 Vestas turbines V90 – 3.0MW … with hub height of 105m and 90m rotor diameter“",
     "u": "https://www.aesbulgaria.com/en/blog/celebrating-tenth-anniversary-bulgarias-largest-wind-farm-st-nikola",
     "ids": [1413283017, 1413283036, 1413283080, 1413283118, 1413283120, 1413283145, 1413283151, 1413283156,
             1413283162, 1413283167, 1413283182, 1413283199, 1413283202, 1413283222, 1413283226, 1413283230,
             1413283234, 1413283246, 1413283254, 1413283280, 1413283283, 1413283306, 1413283309, 1413283331,
             1413283338, 1413283345, 1413283353, 1413283358, 1413283365, 1413283372, 1413283421, 1413283424,
             1413283426, 1413283446, 1413283476, 1413283483, 1413283494, 1413283518, 1413283582, 1413283641,
             1413283656, 1413283663, 1413283711, 1413283735, 1413283749, 1413283757, 1413283769, 2790118398,
             4881517818, 4881518163, 4881576964, 13048843158]},
    {"key": "kaliakra", "n": "Калиакра", "m": "Mitsubishi MWT-1000A", "h": 99.7,
     "src": "ИНОС-1: „35 ветроенергийни генератора, високи 69 m, тип MWT-1000A“; MHI specification: rotor 61.4 m",
     "u": "https://inos1.com/index.php?content=projects&lang=bg&p_category=power_infrastructure",
     "ids": [3754407468, 3754407469, 3754407470, 3754407471, 3754407473, 3754407474, 3754407475, 3754407478,
             3754407479, 3754407480, 3754407482, 3754407483, 3754407484, 3754407489, 3754407492, 3754407494,
             3754407495, 3754407497, 3754407505, 3754407513, 3754407516, 3754407517, 3754407519, 3754407520,
             3754407524, 3754413425, 3754413428, 3754413431, 3754413434, 3754413436, 3754413441, 3754413443,
             3754413444, 3754413446, 3754413448]},
    {"key": "suvorovo", "n": "Суворово", "m": "Gamesa G90-2.0", "h": 125,
     "src": "Eolica Bulgaria: „30 wind turbines Gamesa G90/2 MW with a tower height of 80 m“ (rotor 90 m)",
     "u": "https://web.archive.org/web/20201028170621/http://eolica-bg.com/en/wind-farm-suvorovo.html",
     "ids": [2634483911, 2634483912, 2634483913, 2634483914, 2634483915, 2634483916, 2634483917, 2634483918,
             2634483919, 2634483920, 2634483921, 2634483922, 2634483925, 2634483928, 2634483932, 2634483935,
             2634483939, 2634483942, 2634483946, 2634483948, 2634483949, 2634483953, 2634483956, 2634483959,
             2634483963, 2634483966, 2634483970, 4880063620, 4880063821, 9948919304]},
    {"key": "kardam", "n": "Кардам", "m": "Suzlon S88-2.1", "h": 123,
     "src": "Energy Review 5/2011: „6 вятърни турбини Suzlon S88 … Те работят на височина 79 м с диаметър на ротора 88 м“",
     "u": "https://www.energy-review.bg/bg/pregled-na-realizirani-v-proces-na-realizaciya-i-predstoyashti-proekti-za-izgrazhdane-na-vetroenergiini-centrali-u-nas/2/176/",
     "ids": [9690425486, 9690425487, 9690425488, 9690425489, 9690425490, 9690425491]},
]

# The smallest height of the wires above the ground at their largest sag, in metres:
# [outside settlements, in settlements, over roads]. Наредба № 3 от 9.06.2004 за устройството
# на електрическите уредби и електропроводните линии (last amended ДВ 42/2015): чл. 620 табл. 45
# („Ненаселени“: до 110 kV 6, 220 kV 7, 400 kV 8), чл. 634 табл. 47, чл. 672 табл. 55; low
# voltage чл. 475: „Разстоянието от проводниците до земята при най-големия им провес се приема
# най-малко 6 m.“ A line of unknown voltage takes the lower of 20 kV and low voltage.
WIRE_MIN = {
    400: [8, 9, 9.0],
    220: [7, 8, 8.6],
    110: [6, 7, 7.6],
    20: [6, 7, 7.6],
    0.4: [6, 6, None],
    0: [6, 6, None],
}
WIRE_SRC = "Наредба № 3 от 9.06.2004 (ДВ 90/2004), чл. 475, 620, 634, 672"
WIRE_URL = "https://lex.bg/laws/ldoc/2135493680"

# Railway contact wire: Наредба № 55 от 29.01.2004, чл. 89: „в междугарие - 5600 мм“ above the
# rail head (stations 5800 mm, level crossings 6000 mm).
RAIL_WIRE = {"h": 5.6, "lc": 6.0, "src": "Наредба № 55 от 29.01.2004, чл. 89",
             "u": "https://www.ciela.net/svobodna-zona-normativi/view/2135480496/naredba-%E2%84%96-55-ot-29-yanuari-2004-g-za-proektirane-i-stroitelstvo-na-zhelezopatni-linii-zhelezopatni-gari-zhelezopatni-prelezi-i-drugi-elementi-ot-zhelezopatnata-infrastruktura"}
