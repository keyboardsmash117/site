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
    "FASTCAST": "Fast Cast", "CONSERVE_MP": "Conserve MP",
    "SHIELDBLOCKRATE": "Shield Block Rate",
    "DOUBLE_ATTACK": "Double Attack", "TRIPLE_ATTACK": "Triple Attack",
    "DMG": "Damage Taken reduction",
    "CURE_POTENCY": "Cure Potency",
    "CURE_POTENCY_RCVD": "Cure Potency Received",
    "STORETP": "Store TP", "STORE_TP": "Store TP",
    "SONG_DURATION_BONUS": "Song Duration",
    "DRAGON_KILLER": "Dragon Killer",
    "HASTE_MAGIC": "Magic Haste",
    "REGEN": "Regen", "REFRESH": "Refresh", "REGAIN": "Regain",
    "ENMITY": "Enmity",
    "MND": "MND", "INT": "INT", "STR": "STR", "DEX": "DEX",
    "AGI": "AGI", "VIT": "VIT", "CHR": "CHR",
    "PARRY": "Parry",
    "SUBTLE_BLOW": "Subtle Blow",
    "HASTE": "Haste",
    "ACC": "Accuracy",
    "TH": "Treasure Hunter",
    "AUTO_STEAL": "Auto Steal",
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
        parts.append('<p>Trade <strong>Trust Stones / Gems / Jewels</strong> plus the quest item at the upgrade NPC to progress this trust through tiers.</p>')
        parts.append('<table class="info-table"><tbody>')
        parts.append("  <tr><th>Tier</th><th>Unlocks</th></tr>")
        for t in ("1", "2", "3"):
            if t in tiers:
                bullets = list_abilities(tiers[t])
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
