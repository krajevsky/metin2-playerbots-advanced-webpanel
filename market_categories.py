"""IkarusShop category SQL matching Tieru market_preview.rules.classify.

The IDs, source priority and refine exceptions come from Tieru's read-only
rules.py and sheet.py (2026-10-09 audit). This module builds fixed SQL; no
request text is interpolated into it.
"""

CATEGORIES = (
    (1, "Bronie", "Weapons"),
    (2, "Zbroje", "Armour"),
    (3, "Tarcze i hełmy", "Shields and helmets"),
    (4, "Biżuteria", "Jewellery"),
    (5, "Buty", "Boots"),
    (6, "Księgi umiejętności", "Skill books"),
    (7, "Kamienie duszy", "Soul stones"),
    (8, "Skrzynie", "Chests"),
    (9, "Mikstury i użytkowe", "Potions and usables"),
    (10, "Materiały", "Materials"),
    (11, "Inne", "Other"),
)

# Tieru rules.CATEGORIES: subcategory IDs are scoped to their parent category.
SUBCATEGORIES = {
    1: ((1, "Miecze", "Swords"), (2, "Broń dwuręczna", "Two-handed"),
        (3, "Sztylety", "Daggers"), (4, "Łuki", "Bows"),
        (5, "Dzwony", "Bells"), (6, "Wachlarze", "Fans")),
    3: ((1, "Tarcze", "Shields"), (2, "Hełmy", "Helmets")),
    4: ((1, "Bransolety", "Bracelets"), (2, "Naszyjniki", "Necklaces"),
        (3, "Kolczyki", "Earrings")),
    6: ((1, "Wojownik", "Warrior"), (2, "Ninja", "Ninja"),
        (3, "Sura", "Sura"), (4, "Szaman", "Shaman"),
        (5, "Księgi Zapomnienia", "Forgetting books"),
        (6, "Księgi pasywne", "Passive books")),
    7: tuple((grade + 1, f"+{grade}", f"+{grade}") for grade in range(5)),
    10: ((1, "Ulepszacze", "Upgrade materials"),
         (2, "Rudy i przetopy", "Ores and smelted ores"),
         (3, "Zioła", "Herbs"), (4, "Ryby", "Fish")),
}

CLASS_FILTERS = ((1, "Wojownik", "Warrior"), (2, "Ninja", "Ninja"),
                 (4, "Sura", "Sura"), (8, "Szaman", "Shaman"))

# Tieru market_preview.sheet.REFINE_MATERIALS, including items whose proto
# type is not ITEM_MATERIAL. Keep this explicit instead of assuming a VNUM
# range (there are gaps and other item kinds inside those ranges).
REFINE_MATERIALS = frozenset((
    27799, 27987, 27992, 27993, 27994,
    30003, 30004, 30005, 30006, 30007, 30008, 30009, 30010, 30011,
    30014, 30015, 30016, 30017, 30018, 30019, 30021, 30022, 30023,
    30025, 30027, 30028, 30030, 30031, 30032, 30033, 30034, 30035,
    30037, 30038, 30039, 30040, 30041, 30042, 30045, 30046, 30047,
    30048, 30049, 30050, 30051, 30052, 30053, 30055, 30056, 30057,
    30058, 30059, 30060, 30061, 30067, 30069, 30070, 30071, 30072,
    30073, 30074, 30075, 30076, 30077, 30078, 30079, 30080, 30081,
    30082, 30083, 30084, 30085, 30086, 30087, 30088, 30089, 30090,
    30091, 30092, 30116, 30271, 30343, 30344, 30345, 30346, 30347,
    30348, 30349, 30350, 30351, 30352, 30353, 30354, 30355, 30356,
    30357, 30358, 30359, 30367, 35002,
))


def category_sql():
    """Return the SQL expression for Tieru's eleven top-level categories.

    `i` is player.item and `ip` is player.item_proto in the caller's query.
    Branch order deliberately mirrors rules.classify, including passive books,
    herbs and ores before generic materials and consumables.
    """
    passive = ",".join(str(n) for n in (*range(50301, 50307),
                                        *range(50311, 50317), 50060, 50061, 50600))
    herbs = ",".join(str(n) for n in (*range(50721, 50741), 50056))
    refine = ",".join(str(n) for n in sorted(REFINE_MATERIALS))
    return f"""CASE
      WHEN ip.type=1 THEN IF(ip.subtype IN (0,1,2,3,4,5),1,11)
      WHEN ip.type=2 THEN CASE ip.subtype
        WHEN 0 THEN 2 WHEN 1 THEN 3 WHEN 2 THEN 3
        WHEN 3 THEN 4 WHEN 4 THEN 5 WHEN 5 THEN 4 WHEN 6 THEN 4
        ELSE 11 END
      WHEN ip.type IN (17,22) OR i.vnum IN ({passive}) THEN 6
      WHEN ip.type=10 THEN 7
      WHEN ip.type IN (20,23) THEN 8
      WHEN i.vnum IN ({herbs}) OR i.vnum BETWEEN 50601 AND 50640
        OR ip.type=12 OR i.vnum IN ({refine}) OR ip.type IN (5,14) THEN 10
      WHEN ip.type IN (3,4,36,19) THEN 9
      ELSE 11 END"""


def subcategory_sql():
    """Return Tieru's subcategory expression; combine with category_sql.

    The general skill book stores its skill in socket0; 50401–50599 encode
    the skill in the VNUM. Other skill books fall into passive books.
    """
    skill = "CASE WHEN i.vnum=50300 THEN i.socket0 WHEN i.vnum BETWEEN 50401 AND 50599 THEN i.vnum-50400 ELSE 0 END"
    herbs = ",".join(str(n) for n in (*range(50721, 50741), 50056))
    return f"""CASE
      WHEN ip.type=1 THEN CASE ip.subtype
        WHEN 0 THEN 1 WHEN 3 THEN 2 WHEN 1 THEN 3
        WHEN 2 THEN 4 WHEN 4 THEN 5 WHEN 5 THEN 6 ELSE 0 END
      WHEN ip.type=2 THEN CASE ip.subtype
        WHEN 2 THEN 1 WHEN 1 THEN 2 WHEN 3 THEN 1
        WHEN 5 THEN 2 WHEN 6 THEN 3 ELSE 0 END
      WHEN ip.type=17 THEN CASE
        WHEN ({skill}) BETWEEN 1 AND 5 OR ({skill}) BETWEEN 16 AND 20 THEN 1
        WHEN ({skill}) BETWEEN 31 AND 35 OR ({skill}) BETWEEN 46 AND 51 THEN 2
        WHEN ({skill}) BETWEEN 61 AND 66 OR ({skill}) BETWEEN 76 AND 81 THEN 3
        WHEN ({skill}) BETWEEN 91 AND 96 OR ({skill}) BETWEEN 106 AND 111 THEN 4
        ELSE 6 END
      WHEN ip.type=22 THEN 5
      WHEN i.vnum IN (50060,50061,50600,50301,50302,50303,50304,50305,50306,
                      50311,50312,50313,50314,50315,50316) THEN 6
      WHEN ip.type=10 THEN CASE WHEN i.vnum BETWEEN 28000 AND 28999
        AND MOD(i.vnum DIV 100,10) <= 4 THEN MOD(i.vnum DIV 100,10)+1 ELSE 0 END
      WHEN i.vnum IN ({herbs}) THEN 3
      WHEN i.vnum BETWEEN 50601 AND 50640 THEN 2
      WHEN ip.type=12 THEN 4
      WHEN ({category_sql()})=10 THEN 1
      ELSE 0 END"""


def refine_sql():
    """Tieru rules.split_plus on item_proto.locale_name, as MariaDB SQL."""
    return """CASE WHEN ip.locale_name REGEXP '[+][[:space:]]*[0-9]{1,2}[[:space:]]*$'
      THEN CAST(TRIM(SUBSTRING_INDEX(ip.locale_name,'+',-1)) AS UNSIGNED)
      ELSE -1 END"""


def class_mask_sql():
    """Tieru rules.class_mask from proto antiflags and general-book skill."""
    skill = "CASE WHEN i.vnum=50300 THEN i.socket0 WHEN i.vnum BETWEEN 50401 AND 50599 THEN i.vnum-50400 ELSE 0 END"
    return f"""CASE
      WHEN ip.type=17 THEN CASE
        WHEN ({skill}) BETWEEN 1 AND 5 OR ({skill}) BETWEEN 16 AND 20 THEN 1
        WHEN ({skill}) BETWEEN 31 AND 35 OR ({skill}) BETWEEN 46 AND 51 THEN 2
        WHEN ({skill}) BETWEEN 61 AND 66 OR ({skill}) BETWEEN 76 AND 81 THEN 4
        WHEN ({skill}) BETWEEN 91 AND 96 OR ({skill}) BETWEEN 106 AND 111 THEN 8
        ELSE 15 END
      WHEN ip.type IN (1,2) THEN
        IF((COALESCE(ip.antiflag,0) & 4)=0,1,0)
        + IF((COALESCE(ip.antiflag,0) & 8)=0,2,0)
        + IF((COALESCE(ip.antiflag,0) & 16)=0,4,0)
        + IF((COALESCE(ip.antiflag,0) & 32)=0,8,0)
      ELSE 15 END"""


def required_level_sql():
    """Tieru snapshot.protos: second level limit overwrites the first."""
    return """CASE WHEN ip.limittype1=1 THEN COALESCE(ip.limitvalue1,0)
      WHEN ip.limittype0=1 THEN COALESCE(ip.limitvalue0,0)
      ELSE 0 END"""


# Points from Tieru market_preview/sheet.py BONUS_TIERS (9 October 2026).
BONUS_POINTS = (6, 8, 10, 12, 13, 14, 15, 17, 19, 21, 32, 33, 37, 38, 39,
                40, 41, 43, 44, 45, 46, 47, 48, 63, 64, 65, 67, 68, 69, 70,
                71, 72, 73, 74, 77, 79, 80, 81, 84, 88, 89, 95, 116, 139, 147)
