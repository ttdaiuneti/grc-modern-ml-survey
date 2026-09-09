"""
Generate Figure 1: Research activity per axis (publication year distribution).
Output: figures/activity_by_axis.pdf
"""

import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

os.makedirs("figures", exist_ok=True)

# ── Paper → (year, axis) mapping ──────────────────────────────────────────────
# Axes: 1=Granule Geometry, 2=Topology, 3=Efficiency, 4=Sufficiency/Limits
# Only survey-included papers (those addressing the GrC core pipeline);
# pure background/methodology references are omitted.

PAPERS = {
    # Axis 1 — Granule Geometry
    "Hu2008NRS":               (2008, 1),
    "JensenShen2007TFS":       (2007, 1),
    "Cornelis2010IS":          (2010, 1),
    "QianLiangYaoDang2010MGRS":(2010, 1),
    "LinQianLi2012NMGRS":      (2012, 1),
    "Yao2010threeway":         (2010, 1),
    "Xia2020GBNRS":            (2020, 1),
    "Wang2020selfinfo":        (2020, 1),
    "Xia2021KBSselector":      (2021, 1),
    "Hu2021WNRS":              (2021, 1),
    "Peng2022VPGB":            (2022, 1),
    "Xia2022EfficientGB":      (2022, 1),
    "Ju2023bidirectional":     (2023, 1),
    "Li2023TFS":               (2023, 1),
    "Wang2023ESWA":            (2023, 1),
    "Xia2023GBRS":             (2023, 1),
    "Qian2023InfoFusion":      (2023, 1),
    "Sun2023KBS":              (2023, 1),
    "Zhang2023TKDEincremental":(2023, 1),
    "Xia2024TFS3WC":           (2024, 1),
    "XiaDeyou2024TFS":         (2024, 1),
    "Xie2024TPAMI":            (2024, 1),
    "Qian2024directional":     (2024, 1),
    "Sun2024TFS":              (2024, 1),
    "Zhang2025NN":             (2025, 1),
    "Sun2025EAAI":             (2025, 1),
    "Nguyen2026MHMG":          (2026, 1),

    # Axis 2 — Topological Formalisms (included papers only; background
    # references CohenSteiner2007, Ghrist2008, Carlsson2009, Chazal2009,
    # Edelsbrunner2010, Otter2017, ChazalMichel2021, HenselMoorRieck2021,
    # Pun2022 are cited for context and omitted from the figure)
    "LaiZhang2006":            (2006, 2),
    "Zhu2007covering":         (2007, 2),
    "DeerCornelisYao2016":     (2016, 2),
    "Kindelan2021TDABC":       (2021, 2),
    "ElSafty2021":             (2021, 2),
    "AlShami2022topology":     (2022, 2),
    "AlShami2022supra":        (2022, 2),
    "Yao2023Alexandrov":       (2023, 2),
    "DaiTT2024IFT":            (2024, 2),
    "AlShami2025delta":        (2025, 2),
    "Su2025TDA":               (2025, 2),

    # Axis 3 — Computational Efficiency
    "YuLiu2004":               (2004, 3),
    "Dai2018TFS":              (2018, 3),
    "Xia2021SLR":              (2021, 3),
    "Sowkuntla2021DARA":       (2021, 3),
    "Zheng2021grouping":       (2021, 3),
    "Wan2023TFS":              (2023, 3),
    "Chen2024cascade":         (2024, 3),
    "Luo2025hash":             (2025, 3),

    # Axis 4 — Sufficiency & Limits (background: CoverHart1967,
    # Drakopoulos1995 omitted from figure)
    "Han2024MFII":             (2024, 4),
    "Santos2022overlap":       (2022, 4),
    "Zhang2022PWS":            (2022, 4),
    "Angelopoulos2023CP":      (2023, 4),
    "Wheat2025BER":            (2025, 4),
}

# ── Count by (year, axis) ─────────────────────────────────────────────────────
counts = defaultdict(lambda: defaultdict(int))
for key, (yr, ax) in PAPERS.items():
    counts[yr][ax] += 1

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
plt.savefig("figures/activity_by_axis.pdf", dpi=300, bbox_inches="tight")
plt.savefig("figures/activity_by_axis.png", dpi=200, bbox_inches="tight")
print("Saved figures/activity_by_axis.pdf and .png")
print(f"Total papers plotted: {sum(len([p for p,v in PAPERS.items() if v[1]==a]) for a in axes)}")
