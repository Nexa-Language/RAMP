#!/usr/bin/env python3
"""Merge old 3 leaderboards → RAMP-Basic (2 workloads) + RAMP-Pro.

Output:
  site/assets/data/leaderboard-basic.json  ← Guided + Semi-Guided merged
  site/assets/data/leaderboard-pro.json    ← Autonomous (renamed)
"""
import json, copy
from pathlib import Path

SITE = Path(__file__).parent
DATA = SITE / "assets" / "data"

# ── Step 1: Fix gpt-5.5 T5=0 → 100 in hard data ──────────────────
hard_path = DATA / "leaderboard-hard.json"
with open(hard_path) as f:
    hard = json.load(f)

for entry in hard:
    if entry["model"] == "gpt-5.5" and entry.get("task5", 0) == 0:
        entry["task5"] = 100.0
        # recalculate pipeline_score
        scores = [entry[f"task{i}"] for i in range(6)]
        entry["pipeline_score"] = round(sum(scores) / 6, 2)
        print(f"Fixed gpt-5.5 T5: 0→100, PL={entry['pipeline_score']}")

# Save fixed copy
with open(hard_path, "w") as f:
    json.dump(hard, f, indent=2, ensure_ascii=False)
print(f"Fixed {hard_path}")

# ── Step 2: Load Guided data ─────────────────────────────────────
with open(DATA / "leaderboard.json") as f:
    guided = json.load(f)

# Add workload tag
for e in guided:
    e["workload"] = "Guided"
    e["context"] = "independent"  # each task new context

# ── Step 3: Load Semi-Guided data (fixed) ───────────────────────
with open(hard_path) as f:
    semi = json.load(f)

for e in semi:
    e["workload"] = "Semi-Guided"
    e["context"] = "persistent"  # one context for all tasks
    # ensure consistent fields
    if "pass_score" not in e:
        e["pass_score"] = 0
    if "zero_shot_pass" not in e:
        e["zero_shot_pass"] = False

# ── Step 4: Merge → Basic ───────────────────────────────────────
basic = guided + semi

# Sort by pipeline_score desc within each workload group
basic.sort(key=lambda e: (e.get("workload", ""), -e.get("pipeline_score", 0)))
for i, e in enumerate(basic):
    e["rank"] = i + 1

basic_path = DATA / "leaderboard-basic.json"
with open(basic_path, "w") as f:
    json.dump(basic, f, indent=2, ensure_ascii=False)
print(f"Created {basic_path} ({len(basic)} entries: {len(guided)} Guided + {len(semi)} Semi-Guided)")

# ── Step 5: Rename Hard-Pro → RAMP-Pro ──────────────────────────
pro_path = DATA / "leaderboard-hard-pro.json"
with open(pro_path) as f:
    pro = json.load(f)

for e in pro:
    e["workload"] = "Autonomous"

new_pro_path = DATA / "leaderboard-pro.json"
with open(new_pro_path, "w") as f:
    json.dump(pro, f, indent=2, ensure_ascii=False)
print(f"Created {new_pro_path} ({len(pro)} entries)")

print("\n✅ All leaderboard data ready!")
print(f"  RAMP-Basic: {len(basic)} rows ({len(guided)} Guided + {len(semi)} Semi-Guided)")
print(f"  RAMP-Pro:   {len(pro)} rows (Autonomous)")