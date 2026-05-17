#!/usr/bin/env python3
"""
For each trust HTML page, inject a data-driven "What They Do" section
(ability list, passive mods, and tier upgrades if present).

Pages already manually curated (the ones with 'Tier Upgrades' heading)
are SKIPPED so we don't clobber hand-crafted writing.
"""
import json, re
from pathlib import Path

HTML_DIR = Path(r"C:/Users/PC/scythe-website/trusts")
DATA_FILE = Path(r"C:/Users/PC/scythe-website/_trusts_data.json")

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

def build_html_block(trust_data: dict, trust_name: str) -> str:
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

def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    updated = 0
    skipped = 0
    missing = []
    for stem, info in data.items():
        if stem in MANUAL_OVERRIDE:
            skipped += 1
            continue
        html_path = find_html(stem)
        if not html_path:
            missing.append(stem)
            continue
        original = html_path.read_text(encoding="utf-8")
        block = build_html_block(info, stem)
        new_html = inject(original, block)
        if new_html != original:
            html_path.write_text(new_html, encoding="utf-8")
            updated += 1
    print(f"Updated: {updated}  Skipped (manual): {skipped}  Missing html: {len(missing)}")
    if missing:
        print("Missing:", missing)

if __name__ == "__main__":
    main()
