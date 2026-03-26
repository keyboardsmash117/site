"""Export FFXI server database to JSON for the Scythe website."""
import json
import subprocess
import re
import os

MYSQL = r"C:\Program Files\MariaDB 11.5\bin\mysql.exe"
DB = "xidb"
USER = "root"
PASS = "Xaviebaby22!"
OUT = os.path.join(os.path.dirname(__file__), "data")
MOD_ENUM = os.path.join(os.path.dirname(__file__), "modifier_enum.txt")

os.makedirs(OUT, exist_ok=True)

def query(sql):
    """Run SQL and return list of dicts."""
    result = subprocess.run(
        [MYSQL, "-u", USER, f"-p{PASS}", DB, "--batch", "--raw", "-e", sql],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:200]}")
        return []
    lines = result.stdout.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        vals = line.split("\t")
        row = {}
        for i, h in enumerate(headers):
            v = vals[i] if i < len(vals) else ""
            if v == "NULL":
                v = None
            elif v.isdigit() or (v.startswith("-") and v[1:].isdigit()):
                v = int(v)
            else:
                try:
                    v = float(v)
                except ValueError:
                    pass
            row[h] = v
        rows.append(row)
    return rows

def save(name, data):
    path = os.path.join(OUT, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print(f"  {name}.json: {len(data) if isinstance(data, list) else 'dict'} ({os.path.getsize(path)//1024}KB)")

# Load modifier enum
def load_mod_names():
    mods = {}
    # Human-readable overrides for common mods
    NAMES = {
        1:'DEF',2:'HP',3:'HP%',5:'MP',6:'MP%',8:'STR',9:'DEX',10:'VIT',11:'AGI',
        12:'INT',13:'MND',14:'CHR',23:'Attack',24:'Ranged Attack',25:'Accuracy',
        26:'Ranged Accuracy',27:'Enmity',28:'Magic Atk',29:'Magic Def',30:'Magic Acc',
        31:'Magic Eva',48:'WS Accuracy',62:'Attack%',63:'DEF%',66:'Ranged Attack%',
        68:'Evasion',69:'Ranged DEF',70:'Ranged Evasion',71:'MP Recovered While Healing',
        72:'HP Recovered While Healing',73:'Store TP',160:'Damage Taken',161:'Physical Damage Taken',
        163:'Magic Damage Taken',164:'Ranged Damage Taken',165:'Crit Hit Rate',
        166:'Crit Hit Evasion',167:'Haste (Magic)',168:'Spell Interruption Rate',
        170:'Fast Cast',171:'Delay',173:'Martial Arts',174:'Skillchain Bonus',
        259:'Dual Wield',288:'Double Attack',289:'Triple Attack',302:'Quadruple Attack',
        311:'Magic Damage',355:'Subtle Blow',384:'Haste (Gear)',421:'Crit Damage',
        407:'Fast Cast II',506:'OCC Attacks',507:'OCC Multiplier',
        256:'Save TP',259:'Dual Wield',291:'Counter',292:'Kick Attacks',
        345:'DA Damage',346:'TA Damage',580:'WS Damage',
        841:'Quick Draw Damage',900:'Enhancing Duration',902:'Regen Duration',
        374:'Cure Potency',375:'Cure Potency II',519:'Cure Cast Time',
        37:'Water MAB',38:'Light MAB',39:'Dark MAB',
        49:'Slash Resist',50:'Pierce Resist',51:'Impact Resist',
        54:'Fire Resist',55:'Ice Resist',56:'Wind Resist',57:'Earth Resist',
        58:'Thunder Resist',59:'Water Resist',60:'Light Resist',61:'Dark Resist',
    }
    if os.path.exists(MOD_ENUM):
        with open(MOD_ENUM) as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    name, val = line.split('=', 1)
                    mid = int(val)
                    if mid not in NAMES:
                        NAMES[mid] = name.replace('_', ' ').title()
    return NAMES

MOD_NAMES = load_mod_names()

# === EQUIPMENT ===
print("Exporting equipment...")
equip = query("""
    SELECT ib.itemid as id,
           REPLACE(ib.name, '_', ' ') as name,
           ie.level as lvl, ie.ilevel as ilvl, ie.jobs, ie.slot,
           COALESCE(iw.dmg, 0) as dmg, COALESCE(iw.delay, 0) as delay,
           COALESCE(iw.skill, 0) as skill
    FROM item_basic ib
    JOIN item_equipment ie ON ib.itemid = ie.itemid
    LEFT JOIN item_weapon iw ON ib.itemid = iw.itemid
    WHERE ie.level > 0 OR ie.ilevel > 0
    ORDER BY ie.ilevel DESC, ie.level DESC, ib.itemid
""")
save("equipment", equip)

# === ITEM MODS (stat bonuses per item) ===
print("Exporting item mods...")
raw_mods = query("""
    SELECT itemId, modId, value FROM item_mods ORDER BY itemId, modId
""")
# Group by itemId -> list of {mod, val}
item_mods = {}
for r in raw_mods:
    iid = r['itemId']
    mid = r['modId']
    name = MOD_NAMES.get(mid, f"Mod {mid}")
    if iid not in item_mods:
        item_mods[iid] = []
    item_mods[iid].append({"n": name, "v": r['value']})
save("item_mods", item_mods)

# === ITEMS ===
print("Exporting items...")
items = query("""
    SELECT ib.itemid as id,
           REPLACE(ib.name, '_', ' ') as name,
           ib.stackSize as stack, ib.BaseSell as sell
    FROM item_basic ib
    LEFT JOIN item_equipment ie ON ib.itemid = ie.itemid
    WHERE ie.itemid IS NULL
    AND ib.itemid > 0
    AND ib.name != ''
    ORDER BY ib.itemid
""")
save("items", items)

# === SPELLS ===
print("Exporting spells...")
spells = query("""
    SELECT spellid as id, name, validTargets as target,
           mpCost as mp, castTime as cast, recastTime as recast,
           skill, element
    FROM spell_list
    WHERE spellid > 0
    ORDER BY skill, spellid
""")
save("spells", spells)

# === WEAPON SKILLS ===
print("Exporting weapon skills...")
ws = query("""
    SELECT weaponskillid as id, name, `type`, skilllevel as lvl,
           element, `range` as rng
    FROM weapon_skills
    WHERE weaponskillid > 0
    ORDER BY `type`, skilllevel, weaponskillid
""")
save("weaponskills", ws)

# === MOB SKILLS ===
print("Exporting mob skills...")
mobskills = query("""
    SELECT mob_skill_id as id, mob_skill_name as name,
           mob_skill_aoe as aoe, mob_skill_distance as dist
    FROM mob_skills
    WHERE mob_skill_id > 0
    ORDER BY mob_skill_id
""")
save("mobskills", mobskills)

# === MOBS (with zone, level, family, skills, drops) ===
print("Exporting mobs...")
mobs = query("""
    SELECT mp.poolid as id,
           REPLACE(mp.name, '_', ' ') as name,
           mp.familyid as family,
           mg.zoneid as zone, REPLACE(zs.name, '_', ' ') as zoneName,
           mg.minLevel as minLvl, mg.maxLevel as maxLvl,
           mg.dropid as dropId,
           mp.skill_list_id as skillList,
           mp.spellList as spellList
    FROM mob_pools mp
    JOIN mob_groups mg ON mp.poolid = mg.poolid
    JOIN zone_settings zs ON mg.zoneid = zs.zoneid
    ORDER BY mp.name, mg.zoneid
""")
save("mobs", mobs)

# === ZONES ===
print("Exporting zones...")
zones = query("""
    SELECT zoneid as id, name,
           CASE zonetype & 0xFF
               WHEN 0 THEN 'City' WHEN 1 THEN 'Dungeon'
               WHEN 2 THEN 'Outdoors' WHEN 3 THEN 'Battlefield'
               ELSE 'Other' END as type,
           misc
    FROM zone_settings
    WHERE zoneid > 0
    ORDER BY zoneid
""")
save("zones", zones)

# === NM HUNTS ===
print("Exporting NM hunts...")
spawn_file = r"c:\Users\PC\bla\modules\custom\lua\nm_hunt_spawns.lua"
with open(spawn_file, "r", encoding="utf-8") as f:
    content = f.read()

nms = []
zone_name_map = {z["id"]: z["name"] for z in zones}
zone_blocks = re.split(r'--\s*Zone\s+(\d+)', content)
current_zone = None

for i, block in enumerate(zone_blocks):
    if block.strip().isdigit():
        current_zone = int(block.strip())
        continue
    if current_zone is None:
        continue
    for m in re.finditer(r'name\s*=\s*["\']([^"\']+)["\']', block):
        nm_name = m.group(1)
        nms.append({
            "name": nm_name,
            "zone": current_zone,
            "zoneName": zone_name_map.get(current_zone, f"Zone {current_zone}")
        })

if len(nms) < 100:
    nms = []
    for m in re.finditer(r'name\s*=\s*["\']([^"\']+)["\']', content):
        nms.append({"name": m.group(1)})

save("nm_hunts", nms)

# === DROPS ===
print("Exporting drops...")
drops = query("""
    SELECT REPLACE(mp.name, '_', ' ') as mob,
           REPLACE(zs.name, '_', ' ') as zone,
           REPLACE(ib.name, '_', ' ') as item,
           ib.itemid as itemId,
           md.dropType as type,
           md.groupRate as gRate,
           md.itemRate as iRate
    FROM mob_droplist md
    JOIN item_basic ib ON md.itemId = ib.itemid
    JOIN mob_groups mg ON md.dropId = mg.dropid
    JOIN mob_pools mp ON mg.poolid = mp.poolid
    JOIN zone_settings zs ON mg.zoneid = zs.zoneid
    WHERE md.itemRate > 0
    ORDER BY mp.name, md.dropType, md.groupRate DESC, md.itemRate DESC
""")
save("drops", drops)

# === CRAFTING RECIPES ===
print("Exporting recipes...")
recipes = query("""
    SELECT sr.ID as id,
           REPLACE(ib.name, '_', ' ') as result,
           ib.itemid as resultId,
           sr.ResultQty as qty,
           sr.Crystal as crystal,
           sr.Wood as wood, sr.Smith as smith, sr.Gold as gold,
           sr.Cloth as cloth, sr.Leather as leather, sr.Bone as bone,
           sr.Alchemy as alchemy, sr.Cook as cook,
           sr.Ingredient1 as i1, sr.Ingredient2 as i2,
           sr.Ingredient3 as i3, sr.Ingredient4 as i4,
           sr.Ingredient5 as i5, sr.Ingredient6 as i6,
           sr.Ingredient7 as i7, sr.Ingredient8 as i8
    FROM synth_recipes sr
    JOIN item_basic ib ON sr.Result = ib.itemid
    ORDER BY sr.ID
""")
# Resolve ingredient names
ing_ids = set()
for r in recipes:
    for k in ['i1','i2','i3','i4','i5','i6','i7','i8','crystal']:
        if r[k] and r[k] > 0:
            ing_ids.add(r[k])

if ing_ids:
    id_list = ','.join(str(i) for i in ing_ids)
    ing_names = query(f"SELECT itemid, REPLACE(name, '_', ' ') as name FROM item_basic WHERE itemid IN ({id_list})")
    ing_map = {r['itemid']: r['name'] for r in ing_names}
    for r in recipes:
        ings = []
        for k in ['i1','i2','i3','i4','i5','i6','i7','i8']:
            if r[k] and r[k] > 0:
                ings.append(ing_map.get(r[k], f"Item {r[k]}"))
        r['ingredients'] = ings
        r['crystalName'] = ing_map.get(r['crystal'], '')
        # Craft skill required (highest non-zero)
        craft_skills = []
        for sk, sn in [('wood','Woodworking'),('smith','Smithing'),('gold','Goldsmithing'),
                        ('cloth','Clothcraft'),('leather','Leathercraft'),('bone','Bonecraft'),
                        ('alchemy','Alchemy'),('cook','Cooking')]:
            if r[sk] and r[sk] > 0:
                craft_skills.append(f"{sn} {r[sk]}")
        r['skills'] = ', '.join(craft_skills)
        # Clean up intermediate keys
        for k in ['i1','i2','i3','i4','i5','i6','i7','i8','crystal',
                   'wood','smith','gold','cloth','leather','bone','alchemy','cook']:
            del r[k]

save("recipes", recipes)

# === ITEM -> DROP CROSS-REFERENCE (which mobs drop this item) ===
print("Building item drop index...")
item_drops = {}
for r in drops:
    iid = r['itemId']
    if iid not in item_drops:
        item_drops[iid] = []
    pct = round((r['gRate'] / 1000) * (r['iRate'] / 1000) * 100, 1)
    item_drops[iid].append({"mob": r['mob'], "zone": r['zone'], "pct": pct})
save("item_drops", item_drops)

print(f"\nDone! All data in {OUT}/")
