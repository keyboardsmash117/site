#!/usr/bin/env python3
"""
For each trust HTML page, inject a data-driven "What They Do" section
(ability list, passive mods, tier upgrades, and quest requirements if present).

Pages already manually curated (the ones with 'Tier Upgrades' heading)
keep their hand-crafted writing and only receive the generated requirements block.
"""
import json, re
from html import escape
from pathlib import Path

HTML_DIR = Path(r"C:/Users/PC/scythe-website/trusts")
DATA_FILE = Path(r"C:/Users/PC/scythe-website/_trusts_data.json")
SERVER_ROOT = Path(r"C:/Users/PC/bla")
QUEST_DATA_FILE = SERVER_ROOT / "modules/custom/lua/trust_quest_data.lua"
ITEM_ENUM_FILE = SERVER_ROOT / "scripts/enum/item.lua"

REQ_BEGIN = "<!-- TRUST-REQ-BEGIN -->"
REQ_END = "<!-- TRUST-REQ-END -->"

QUEST_KEY_TO_STEM = {
    "Ark EV": "aaev",
    "Ark GK": "aagk",
    "Ark HM": "aahm",
    "Ark MR": "aamr",
    "Ark TT": "aatt",
    "Apururu": "apururu_uc",
    "Yoran": "yoran-oran_uc",
    "Mihli": "mihli_aliapoh",
    "Pieuje": "pieuje_uc",
    "Karaha": "karaha-baruha",
    "Sylvie": "sylvie_uc",
    "Uka": "uka_totlihn",
    "I.Shield": "i_shield_uc",
    "Naja": "naja_salaheem",
    "Naja UC": "naja_uc",
    "Lhe": "lhe_lhangavo",
    "Lhu": "lhu_mhakaracca",
    "Jakoh UC": "jakoh_uc",
    "Flaviria": "flaviria_uc",
    "Ajido": "ajido-marujido",
    "Semih": "semih_lafihna",
    "Makki": "makki-chebukki",
    "Lehko": "lehko_habhoka",
    "Kukki": "kukki-chebukki",
    "Kayeel": "kayeel-payeel",
    "Kuyin": "kuyin_hathdenna",
}

NATIONS = {
    "0": "San d'Oria",
    "1": "Bastok",
    "2": "Windurst",
    "SANDY": "San d'Oria",
    "BASTOK": "Bastok",
    "WINDY": "Windurst",
}

FAME_AREAS = {
    "0": "San d'Oria",
    "1": "Bastok",
    "2": "Windurst",
    "3": "Jeuno",
    "4": "Norg",
    "5": "Aht Urhgan",
    "6": "Adoulin",
}

JOBS = {
    "1": "WAR",
    "2": "MNK",
    "3": "WHM",
    "4": "BLM",
    "5": "RDM",
    "6": "THF",
    "7": "PLD",
    "8": "DRK",
    "9": "BST",
    "10": "BRD",
    "11": "RNG",
    "12": "SAM",
    "13": "NIN",
    "14": "DRG",
    "15": "SMN",
    "16": "BLU",
    "17": "COR",
    "18": "PUP",
    "19": "DNC",
    "20": "SCH",
    "21": "GEO",
    "22": "RUN",
}

CRAFTS = {
    "48": "Fishing",
    "49": "Woodworking",
    "50": "Smithing",
    "51": "Goldsmithing",
    "52": "Clothcraft",
    "53": "Leathercraft",
    "54": "Bonecraft",
    "55": "Alchemy",
    "56": "Cooking",
    "57": "Synergy",
}

CURRENCY_BY_TIER = {
    1: "5 Trust Stones",
    2: "10 Trust Gems",
    3: "5 Trust Jewels",
}

TIER_LABELS = {
    1: "Tier I",
    2: "Tier II",
    3: "Tier III (MAX)",
}

# Friendly name overrides — enum names that don't humanise cleanly.
FRIENDLY = {
    "HPP_LT": "low HP", "MPP_LT": "low MP",
    "HP": "HP", "MPP": "MP", "HPP": "HP",
    "MATT": "Magic Attack", "MACC": "Magic Accuracy",
    "MEVA": "Magic Evasion", "MDEF": "Magic Defense",
    "DEF": "Defense", "ATT": "Attack",
    "RATT": "Ranged Attack", "RACC": "Ranged Accuracy",
    "FASTCAST": "Fast Cast", "CONSERVE_MP": "Conserve MP",
    "SHIELDBLOCKRATE": "Shield Block Rate",
    "DOUBLE_ATTACK": "Double Attack", "TRIPLE_ATTACK": "Triple Attack",
    "DMG": "Damage Taken reduction",
    "ALL_WSDMG_ALL_HITS": "Weapon Skill Damage",
    "SKILLCHAINDMG": "Skillchain Damage",
    "CRITHITRATE": "Critical Hit Rate",
    "CURE_POTENCY": "Cure Potency",
    "CURE_POTENCY_RCVD": "Cure Potency Received",
    "ENHANCES_CURSNA": "Cursna Potency",
    "ENH_DRAIN_ASPIR": "Drain/Aspir Potency",
    "ENH_MAGIC_DURATION": "Enhancing Magic Duration",
    "STORETP": "Store TP", "STORE_TP": "Store TP",
    "SONG_DURATION_BONUS": "Song Duration",
    "ALL_SONGS_EFFECT": "Song Potency",
    "MAXIMUM_SONGS_BONUS": "Maximum Songs",
    "DRAGON_KILLER": "Dragon Killer",
    "HASTE_MAGIC": "Magic Haste",
    "HASTE_GEAR": "Gear Haste",
    "REGEN": "Regen", "REFRESH": "Refresh", "REGAIN": "Regain",
    "REGEN_DURATION": "Regen Duration",
    "ENMITY": "Enmity",
    "MND": "MND", "INT": "INT", "STR": "STR", "DEX": "DEX",
    "AGI": "AGI", "VIT": "VIT", "CHR": "CHR",
    "PARRY": "Parry",
    "SUBTLE_BLOW": "Subtle Blow",
    "HASTE": "Haste",
    "ACC": "Accuracy",
    "EVA": "Evasion",
    "TH": "Treasure Hunter",
    "TREASURE_HUNTER": "Treasure Hunter",
    "AUTO_STEAL": "Auto Steal",
    "GEOMANCY_BONUS": "Geomancy Bonus",
    "INDI_DURATION": "Indi Duration",
    "ENSPELL_DMG": "Enspell Damage",
    "ENSPELL_DMG_BONUS": "Enspell Damage",
    "MAGIC_BURST_BONUS_UNCAPPED": "Magic Burst Damage",
    "MAGIC_DAMAGE": "Magic Damage",
    "SAVETP": "Save TP",
    "WALTZ_POTENCY": "Waltz Potency",
    "KICK_ATTACK_RATE": "Kick Attack Rate",
    "COUNTER": "Counter",
    "JUMP_TP_BONUS": "Jump TP Bonus",
    "WARCRY_DURATION": "Warcry Duration",
    "CAPACITY_BONUS": "Capacity Point Bonus",
    "EXP_BONUS": "EXP Bonus",
    "GILFINDER": "Gilfinder",
    "CHARMRES": "Charm Resist",
    "FIRE_MEVA": "Fire Magic Evasion",
    "ICE_MEVA": "Ice Magic Evasion",
    "WIND_MEVA": "Wind Magic Evasion",
    "EARTH_MEVA": "Earth Magic Evasion",
    "THUNDER_MEVA": "Thunder Magic Evasion",
    "WATER_MEVA": "Water Magic Evasion",
    "LIGHT_MEVA": "Light Magic Evasion",
    "DARK_MEVA": "Dark Magic Evasion",
    "LIGHT_MAB": "Light Magic Attack",
    "DARK_MAB": "Dark Magic Attack",
    "EARTH_MAB": "Earth Magic Attack",
}

# Known abbreviations that should stay uppercase
KEEP_UPPER = {"TP", "HP", "MP", "AF", "MND", "INT", "STR", "DEX", "AGI", "VIT", "CHR",
              "II", "III", "IV", "V", "VI", "COR", "WHM", "BLM", "RDM", "PLD", "DRK",
              "WAR", "MNK", "THF", "BRD", "RNG", "SAM", "NIN", "DRG", "SMN", "BLU",
              "PUP", "DNC", "SCH", "GEO", "RUN", "BST"}

def normalize_lookup(text: str) -> str:
    text = text.lower().replace("&amp;", "and")
    text = re.sub(r"\bark angel\b", "ark", text)
    text = text.replace("'", "")
    return re.sub(r"[^a-z0-9]+", "", text)

def load_page_title_map() -> dict:
    titles = {}
    for path in HTML_DIR.glob("*.html"):
        content = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'<h1 class="page-title">([^<]+)</h1>', content)
        if match:
            titles[normalize_lookup(match.group(1))] = path.stem
    return titles

def load_item_enum_names() -> dict:
    if not ITEM_ENUM_FILE.exists():
        return {}

    enum_names = {}
    for line in ITEM_ENUM_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.search(r"\b([A-Z0-9_]+)\s*=\s*(\d+),", line)
        if match:
            enum_names[int(match.group(2))] = match.group(1)
    return enum_names

def humanise_item_enum(enum_name: str) -> str:
    if not enum_name:
        return ""

    enum_name = re.sub(r"_P([123])\b", r"_+\1", enum_name)
    pieces = []
    for piece in enum_name.split("_"):
        if not piece:
            continue
        if piece.startswith("+") or piece.isdigit() or piece in KEEP_UPPER:
            pieces.append(piece)
        else:
            pieces.append(piece.capitalize())
    return " ".join(pieces)

def clean_requirement_desc(desc: str, qty: int) -> str:
    desc = desc.replace("\\'", "'").replace("â€™", "'").replace("’", "'")
    desc = re.sub(r"\s+\+\s+(?:San d'Oria|Bastok|Windurst)\s+Rank\s+\d+\s*$", "", desc)
    if qty > 1:
        desc = re.sub(rf"\s+x{qty}\b", "", desc)
    return re.sub(r"\s+", " ", desc).strip()

def split_item_note(desc: str) -> tuple[str, str]:
    match = re.match(r"(.+?)\s*\(([^)]*)\)\s*$", desc)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return desc, ""

def exact_item_name(base_name: str, item_id: int, enum_names: dict) -> str:
    enum_pretty = humanise_item_enum(enum_names.get(item_id, ""))
    if not enum_pretty:
        return base_name

    base_norm = normalize_lookup(base_name)
    enum_norm = normalize_lookup(enum_pretty)
    if enum_norm.startswith(base_norm) and enum_norm != base_norm:
        return enum_pretty
    return base_name

def format_trade_item(item_id: int, qty: int, desc: str, enum_names: dict) -> str:
    cleaned = clean_requirement_desc(desc, qty)
    base_name, note = split_item_note(cleaned)
    item_name = exact_item_name(base_name, item_id, enum_names)

    if note:
        detail = f"{note}; item ID {item_id}"
    else:
        detail = f"item ID {item_id}"

    return f"{qty}x {item_name} ({detail})"

def parse_conditions(conds: str | None) -> list[str]:
    if not conds:
        return []

    out = []
    for nation, rank in re.findall(r"rank\(([^,]+),\s*(\d+)\)", conds):
        out.append(f"{NATIONS.get(nation.strip(), nation.strip())} Rank {rank}")
    for job_id, level in re.findall(r"job\(([^,]+),\s*(\d+)\)", conds):
        out.append(f"{JOBS.get(job_id.strip(), 'Job ' + job_id.strip())} level {level}+")
    for level in re.findall(r"anyjob\((\d+)\)", conds):
        out.append(f"Any job level {level}+")
    for skill_id, level in re.findall(r"craft\(([^,]+),\s*(\d+)\)", conds):
        out.append(f"{CRAFTS.get(skill_id.strip(), 'Craft skill ' + skill_id.strip())} skill {level}+")
    for area, level in re.findall(r"fame\(([^,]+),\s*(\d+)\)", conds):
        out.append(f"{FAME_AREAS.get(area.strip(), 'Area ' + area.strip())} fame level {level}")
    for var_name, count in re.findall(r"kills\('([^']+)',\s*(\d+)\)", conds):
        out.append(f"{var_name} kills: {count}+")
    for var_name, minimum in re.findall(r"charvar\('([^']+)',\s*(\d+)\)", conds):
        out.append(f"{var_name} at least {minimum}")
    return out

def parse_trust_requirements() -> dict:
    if not QUEST_DATA_FILE.exists():
        return {}

    enum_names = load_item_enum_names()
    page_titles = load_page_title_map()
    requirements = {}
    current_key = None

    quest_re = re.compile(r"\s*questData\['([^']+)'\]\s*=\s*\{")
    tier_re = re.compile(
        r'T([123])\((\d+),\s*(\d+),\s*([\'"])((?:\\.|(?!\4).)*)\4(?:,\s*(\{.*\}))?\s*\),'
    )

    for line in QUEST_DATA_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        quest_match = quest_re.match(line)
        if quest_match:
            current_key = quest_match.group(1)
            continue

        if current_key is None:
            continue

        if line.strip().startswith("}"):
            current_key = None
            continue

        tier_match = tier_re.search(line)
        if not tier_match:
            continue

        tier = int(tier_match.group(1))
        item_id = int(tier_match.group(2))
        item_qty = int(tier_match.group(3))
        desc = tier_match.group(5)
        conds = tier_match.group(6)

        stem = QUEST_KEY_TO_STEM.get(current_key) or page_titles.get(normalize_lookup(current_key))
        if not stem:
            continue

        requirements.setdefault(stem, []).append({
            "tier": tier,
            "currency": CURRENCY_BY_TIER[tier],
            "trade_item": format_trade_item(item_id, item_qty, desc, enum_names),
            "conditions": parse_conditions(conds),
        })

    return requirements

def build_requirements_block(requirements: list[dict], with_sentinel: bool = False) -> str:
    if not requirements:
        return ""

    parts = [
        '<h3 style="color: var(--text-bright); margin: 2rem 0 1rem;">Upgrade Requirements</h3>',
        '<p>These are the exact items and extra gates checked by the upgrade NPC. Trust currency is stored on your character, not in inventory.</p>',
        '<table class="info-table"><tbody>',
        '  <tr><th>Tier</th><th>Currency</th><th>Trade Item</th><th>Extra Requirement</th></tr>',
    ]

    for req in sorted(requirements, key=lambda item: item["tier"]):
        condition = ", ".join(req["conditions"]) if req["conditions"] else "None"
        parts.append(
            "  <tr>"
            f"<td>{escape(TIER_LABELS[req['tier']])}</td>"
            f"<td>{escape(req['currency'])}</td>"
            f"<td>{escape(req['trade_item'])}</td>"
            f"<td>{escape(condition)}</td>"
            "</tr>"
        )

    parts.append("</tbody></table>")
    block = "\n        ".join(parts)
    if with_sentinel:
        return f"{REQ_BEGIN}\n        {block}\n        {REQ_END}"
    return block

# Spell / JA enums we want to present in English. Fallback: title-case.
def humanise(enum: str) -> str:
    if enum in FRIENDLY:
        return FRIENDLY[enum]
    words = enum.split("_")
    out = []
    for w in words:
        if w in KEEP_UPPER:
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)

def fmt_mod_value(mod_name: str, raw: str) -> str:
    """Convert raw lua value to human-readable. DMG uses /10 for % DT reduction."""
    if mod_name == "DMG":
        try:
            val = int(raw)
            pct = abs(val) / 10
            return f"{pct:.0f}% DT reduction" if val < 0 else f"+{pct:.0f}% damage"
        except ValueError:
            return raw
    if mod_name == "HASTE_MAGIC":
        try:
            return f"{int(raw)/100:.0f}% Magic Haste"
        except ValueError:
            return raw
    if "math.floor" in raw or "mob:" in raw:
        return "scaled to character level"
    return raw

def format_mod(mod):
    name, raw = mod
    pretty = humanise(name)
    val = fmt_mod_value(name, raw)
    if name == "DMG":
        return val  # already phrased as "X% DT reduction"
    if name.startswith("HPP"):
        return f"+{val}% max HP"
    if name == "MPP":
        return f"+{val}% max MP"
    if name == "HP":
        return f"+{val} HP"
    if raw.startswith("-"):
        return f"{val} {pretty}"
    try:
        n = int(raw)
        return f"+{n} {pretty}"
    except ValueError:
        return f"{pretty}: {val}"

def list_abilities(section: dict) -> list:
    """Return a list of human-readable bullet points for this section."""
    pieces = []
    # JAs
    if section["jas"]:
        jas = ", ".join(humanise(j) for j in section["jas"])
        pieces.append(f"Job abilities: {jas}")
    # Cast spells / families
    casts = list(dict.fromkeys(
        [humanise(s) for s in section["spells"]] +
        [humanise(s) + " family" for s in section["spell_families"]]
    ))
    # Filter out trust-name casts (caster name patterns like TRION / CURILLA that remain)
    # Teamwork-message stripping already handles most. Keep what's left.
    if casts:
        pieces.append(f"Spells: {', '.join(casts)}")
    # Spells explicitly added via addSpell
    if section["spells_added"]:
        adds = ", ".join(humanise(s) for s in section["spells_added"])
        pieces.append(f"New spells unlocked: {adds}")
    # Mods
    if section["mods"]:
        mods = ", ".join(format_mod(m) for m in section["mods"])
        pieces.append(f"Passive: {mods}")
    # Tiered mods
    if section["tiered_mods"]:
        tm = ", ".join(humanise(m) for m in section["tiered_mods"])
        pieces.append(f"Tier-scaling stat: {tm} (1.0× → 2.5×)")
    if section["has_enmity_siphon"]:
        pieces.append("Tank enmity siphon (Scythe-custom: drains enmity from party onto this trust every ~3s while engaged)")
    return pieces

def empty_section() -> dict:
    return {
        "spells": [],
        "spell_families": [],
        "jas": [],
        "mods": [],
        "tiered_mods": [],
        "has_enmity_siphon": False,
        "spells_added": [],
    }

def extend_unique(target: list, source: list):
    for item in source:
        if item not in target:
            target.append(item)

def merge_sections(current: dict, extra: dict) -> dict:
    merged = {
        "spells": list(current["spells"]),
        "spell_families": list(current["spell_families"]),
        "jas": list(current["jas"]),
        "mods": list(current["mods"]),
        "tiered_mods": list(current["tiered_mods"]),
        "has_enmity_siphon": current["has_enmity_siphon"] or extra["has_enmity_siphon"],
        "spells_added": list(current["spells_added"]),
    }

    extend_unique(merged["spells"], extra["spells"])
    extend_unique(merged["spell_families"], extra["spell_families"])
    extend_unique(merged["jas"], extra["jas"])
    extend_unique(merged["tiered_mods"], extra["tiered_mods"])
    extend_unique(merged["spells_added"], extra["spells_added"])

    mod_totals = {}
    mod_order = []
    non_numeric = []
    for name, raw in merged["mods"] + extra["mods"]:
        try:
            value = int(raw)
        except ValueError:
            non_numeric.append((name, raw))
            continue

        if name not in mod_totals:
            mod_order.append(name)
            mod_totals[name] = 0
        mod_totals[name] += value

    merged["mods"] = [(name, str(mod_totals[name])) for name in mod_order] + non_numeric
    return merged

def build_html_block(trust_data: dict, trust_name: str, requirements: list[dict] | None = None) -> str:
    base_items = list_abilities(trust_data["base"])
    tiers = trust_data.get("tiers", {})

    parts = ['<h3 style="color: var(--text-bright); margin: 2rem 0 1rem;">Ability Summary</h3>']
    if base_items:
        parts.append("<ul class=\"content-list\">")
        for it in base_items:
            parts.append(f"  <li>{it}</li>")
        parts.append("</ul>")
    else:
        parts.append("<p><em>Base behaviour: standard retail AI. See individual spell lua for detailed gambit list.</em></p>")

    if tiers:
        parts.append('<h3 style="color: var(--text-bright); margin: 2rem 0 1rem;">Scythe Tier Upgrades</h3>')
        parts.append('<p>Trade <strong>Trust Stones / Gems / Jewels</strong> plus the quest item at the upgrade NPC to progress this trust through tiers. Rows show the active bonuses after lower-tier bonuses are included.</p>')
        parts.append('<table class="info-table"><tbody>')
        parts.append("  <tr><th>Tier</th><th>Unlocks</th></tr>")
        cumulative = empty_section()
        for t in ("1", "2", "3"):
            if t in tiers:
                cumulative = merge_sections(cumulative, tiers[t])
                bullets = list_abilities(cumulative)
                if bullets:
                    label = f"Tier {'I' * int(t)}"
                    if t == "3":
                        label += " (MAX)"
                    body = "<br>".join(bullets)
                    parts.append(f"  <tr><td>{label}</td><td>{body}</td></tr>")
        parts.append('</tbody></table>')
        if requirements:
            parts.append(build_requirements_block(requirements))
    return "\n        ".join(parts)

# Mapping file-stem → HTML filename variations (they match 1:1 today)
def find_html(stem: str) -> Path | None:
    target = HTML_DIR / f"{stem}.html"
    if target.exists():
        return target
    return None

# Sentinel comments let us idempotently re-apply.
BEGIN = "<!-- AUTO-TRUST-BEGIN -->"
END = "<!-- AUTO-TRUST-END -->"

MANUAL_OVERRIDE = {  # Pages we handcrafted — skip auto-injection
    "zeid", "zeid_ii", "lion", "lion_ii",
    "nashmeira_ii", "apururu_uc", "august",
    "curilla", "king_of_hearts", "koru-moru",
    "ovjang", "qultada", "shantotto",
    "brygid", "cornelia", "kupofried", "kuyin_hathdenna",
    "moogle", "sakura",
}

INJECT_AFTER_MARKERS = [
    ('<h3 style="color: var(--text-bright); margin: 2rem 0 1rem;">When to Use', "before"),
    ("<p style=\"margin-top: 2rem;\"><a href=\"../trusts.html\">", "before"),
    ('<p style="margin-top: 2rem;">\n            <a href="../trusts.html">', "before"),
]

def inject(html: str, block: str) -> str:
    wrapped = f"{BEGIN}\n        {block}\n        {END}\n\n        "
    # Idempotent: replace existing block between sentinels
    if BEGIN in html and END in html:
        return re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END) + r"\s*",
            wrapped.rstrip() + "\n        ",
            html,
            count=1,
            flags=re.DOTALL,
        )
    # Fresh insert: find a landmark to inject before
    for marker, mode in INJECT_AFTER_MARKERS:
        idx = html.find(marker)
        if idx != -1:
            return html[:idx] + wrapped + html[idx:]
    # As a last resort, insert right before the closing `</div></section>` after the first <section class="section">
    m = re.search(r"(<section class=\"section\">.*?)(\s*<p style=\"margin-top: 2rem;\"><a href=\"\.\./trusts\.html)",
                  html, re.DOTALL)
    if m:
        return html[:m.start(2)] + "\n        " + wrapped.rstrip() + html[m.start(2):]
    return html  # give up silently

def inject_requirements(html: str, block: str) -> str:
    if not block:
        return html

    wrapped = block.rstrip() + "\n\n        "
    if REQ_BEGIN in html and REQ_END in html:
        return re.sub(
            re.escape(REQ_BEGIN) + r".*?" + re.escape(REQ_END) + r"\s*",
            wrapped,
            html,
            count=1,
            flags=re.DOTALL,
        )

    for marker, _mode in INJECT_AFTER_MARKERS:
        idx = html.find(marker)
        if idx != -1:
            return html[:idx] + wrapped + html[idx:]

    return html

def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    requirements = parse_trust_requirements()
    updated = 0
    skipped = 0
    missing = []
    missing_requirements = []
    for stem, info in data.items():
        html_path = find_html(stem)
        if not html_path:
            missing.append(stem)
            continue
        original = html_path.read_text(encoding="utf-8")
        reqs = requirements.get(stem)
        if not reqs:
            missing_requirements.append(stem)

        if stem in MANUAL_OVERRIDE:
            skipped += 1
            new_html = inject_requirements(original, build_requirements_block(reqs or [], with_sentinel=True))
        else:
            block = build_html_block(info, stem, reqs)
            new_html = inject(original, block)
        if new_html != original:
            html_path.write_text(new_html, encoding="utf-8")
            updated += 1
    print(f"Updated: {updated}  Skipped (manual): {skipped}  Missing html: {len(missing)}")
    if missing:
        print("Missing:", missing)
    if missing_requirements:
        print("Missing requirements:", missing_requirements)

if __name__ == "__main__":
    main()
