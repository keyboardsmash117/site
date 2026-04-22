#!/usr/bin/env python3
"""Extract ability data from every trust lua into JSON."""
import re, json
from pathlib import Path

TRUST_DIR = Path(r"c:/Users/PC/bla/scripts/actions/spells/trust")
OUT_FILE  = Path(r"C:/Users/PC/scythe-website/_trusts_data.json")

def strip_teamwork(text: str) -> str:
    """Remove the xi.trust.teamworkMessage(...) block since its spell refs are partner names."""
    return re.sub(
        r"xi\.trust\.teamworkMessage\s*\(\s*mob\s*,\s*\{[^}]*\}\s*\)",
        "",
        text,
        flags=re.DOTALL,
    )

def split_tiers(body_lines):
    tiers = {1: [], 2: [], 3: []}
    base = []
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        m = re.match(r"(\s*)if\s+tier\s*>=\s*(\d+)\s+then", line)
        if m:
            indent, tier_n = m.group(1), int(m.group(2))
            end_pat = re.compile(r"^" + re.escape(indent) + r"end\b")
            j = i + 1
            captured = []
            while j < len(body_lines):
                if end_pat.match(body_lines[j]):
                    break
                captured.append(body_lines[j])
                j += 1
            if tier_n in tiers:
                tiers[tier_n].extend(captured)
            i = j + 1
        else:
            base.append(line)
            i += 1
    return "\n".join(base), {k: "\n".join(v) for k, v in tiers.items()}

def enum_list(block, prefix):
    pat = re.compile(rf"{prefix}\.([A-Z0-9_]+)")
    seen = []
    for m in pat.finditer(block):
        v = m.group(1)
        if v not in seen:
            seen.append(v)
    return seen

def mod_list(block):
    pat = (
        r"addMod\s*\(\s*(?:mob\s*,\s*)?xi\.mod\.([A-Z_]+)\s*,\s*"
        r"(-?\d+|math\.floor[^)]+\)|[A-Za-z_][A-Za-z0-9_\.\s\(\)\+\-\*]*)"
        r"\s*\)"
    )
    out = []
    for m in re.finditer(pat, block):
        out.append((m.group(1), m.group(2).strip()))
    return out

def summarize(block):
    block = strip_teamwork(block)
    return {
        "spells": enum_list(block, r"xi\.magic\.spell"),
        "spell_families": enum_list(block, r"xi\.magic\.spellFamily"),
        "jas": enum_list(block, r"xi\.ja"),
        "mods": mod_list(block),
        "tiered_mods": re.findall(r"applyTieredMod\s*\(\s*mob\s*,\s*xi\.mod\.([A-Z_]+)", block),
        "has_enmity_siphon": "setupEnmitySiphon" in block,
        "spells_added": re.findall(r"addSpell\s*\(\s*xi\.magic\.spell\.([A-Z0-9_]+)", block),
    }

def clean_doc(text: str) -> str:
    lines = text.splitlines()[:8]
    docs = []
    for l in lines:
        s = l.strip().lstrip("-").strip()
        if not s or s.startswith("@") or s.startswith("Trust:"):
            continue
        if "TSpellTrust" in s:
            continue
        docs.append(s)
    return " ".join(docs)[:200]

def analyze(lua_path):
    text = lua_path.read_text(encoding="utf-8", errors="replace")
    doc = clean_doc(text)
    m = re.search(
        r"spellObject\.onMobSpawn\s*=\s*function\s*\(mob\)\s*\n(.*?)\nend\s*\n",
        text, re.DOTALL,
    )
    body = m.group(1) if m else ""
    body_lines = body.splitlines()
    base_block, tier_blocks = split_tiers(body_lines)
    tiers = {}
    for k, v in tier_blocks.items():
        if v.strip():
            s = summarize(v)
            # Skip tiers with literally nothing interesting
            if any([s["spells"], s["spell_families"], s["jas"], s["mods"], s["spells_added"], s["tiered_mods"]]):
                tiers[str(k)] = s
    return {
        "doc": doc,
        "base": summarize(base_block),
        "tiers": tiers,
    }

def main():
    results = {}
    for lua in sorted(TRUST_DIR.glob("*.lua")):
        try:
            results[lua.stem] = analyze(lua)
        except Exception as e:
            print(f"FAIL {lua.stem}: {e}")
    OUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_FILE} ({len(results)} trusts)")

if __name__ == "__main__":
    main()
