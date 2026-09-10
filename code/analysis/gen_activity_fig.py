"""
Generate Figure 1: Research activity per axis (publication year distribution).
Output: figures/activity_by_axis.pdf
"""

import os, csv, matplotlib
matplotlib.use("Agg")
# Embed real (TrueType) fonts, not Type 3 bitmaps, so the PDF passes
# publisher preflight.
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

OUT = os.environ.get("GRC_FIGURES_OUT", "figures")
os.makedirs(OUT, exist_ok=True)

DATA = os.environ.get("GRC_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data") + os.sep)

# ── Axis per paper is read from the released corpus log, not hand-copied ─────
# Axes: 1=Granule Geometry, 2=Topology (2a+2b merged), 3=Efficiency,
# 4=Sufficiency/Limits (the single truc=5 row is folded in here too --
# it is a Gini-index NRS variant with no home axis of its own).
# This keeps the figure from silently drifting out of sync with the corpus
# whenever literature_log.csv gains, loses or re-axes a paper.

def axis_of(truc):
    truc = truc.strip()
    if truc.startswith("2"):
        return 2
    if truc == "5":
        return 4
    return int(truc)

with open(os.path.join(DATA, "literature_log.csv")) as f:
    rows = list(csv.DictReader(f))

counts = defaultdict(lambda: defaultdict(int))
for r in rows:
    yr = int(r["year"])
    ax = axis_of(r["truc"])
    counts[yr][ax] += 1

print(f"Loaded {len(rows)} corpus papers from literature_log.csv "
      f"(axis totals: {dict(sorted((a, sum(counts[y][a] for y in counts)) for a in (1,2,3,4)))})")

# Show only 2006-2026 (exclude ancient foundational refs 1967, 1995)
years = list(range(2006, 2027))
axes  = [1, 2, 3, 4]
labels = [
    "Axis 1: Granule Geometry",
    "Axis 2: Topological Formalisms",
    "Axis 3: Computational Efficiency",
    "Axis 4: Sufficiency & Limits",
]
colors = ["#2166ac", "#d6604d", "#4dac26", "#8073ac"]

data = np.array([[counts[yr][ax] for yr in years] for ax in axes])

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax_main = plt.subplots(figsize=(11, 3.4))

n_groups = len(years)
n_bars   = len(axes)
width    = 0.18
x        = np.arange(n_groups)

for i, (ax_id, label, color) in enumerate(zip(axes, labels, colors)):
    offset = (i - (n_bars - 1) / 2) * width
    bars = ax_main.bar(x + offset, data[i], width=width, color=color,
                       alpha=0.88, label=label, edgecolor="white", linewidth=0.4)

ax_main.set_xticks(x)
ax_main.set_xticklabels(years, rotation=45, ha="right", fontsize=8)
ax_main.set_ylabel("Papers included in survey", fontsize=9)
ax_main.set_ylim(0, data.max() + 1.4)
ax_main.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
ax_main.grid(axis="y", linewidth=0.5, alpha=0.5, linestyle="--")
ax_main.set_axisbelow(True)
ax_main.spines[["top", "right"]].set_visible(False)

legend = ax_main.legend(
    handles=[mpatches.Patch(color=c, alpha=0.88, label=l)
             for c, l in zip(colors, labels)],
    fontsize=8, loc="upper left", framealpha=0.9,
    ncol=2, columnspacing=1.0, handlelength=1.2,
)

# Shade 2020-2026 as "surge period"
ax_main.axvspan(x[years.index(2020)] - 0.45, x[-1] + 0.45,
                alpha=0.06, color="gray", label="_nolegend_")
ax_main.text(x[years.index(2020)] + 0.05, data.max() + 0.85,
             "Axis 1 surge", fontsize=7.5, color="gray", style="italic")

plt.tight_layout(pad=0.4)
plt.savefig(f"{OUT}/activity_by_axis.pdf", dpi=300, bbox_inches="tight")
plt.savefig(f"{OUT}/activity_by_axis.png", dpi=200, bbox_inches="tight")
print(f"Saved {OUT}/activity_by_axis.pdf and .png")
plotted = int(data.sum())
print(f"Total papers plotted: {plotted} (of {len(rows)} in the corpus; "
      f"{len(rows) - plotted} fall outside {years[0]}-{years[-1]} and are not shown)")
