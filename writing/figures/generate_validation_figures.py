"""Generate validation figures for Vecta-DWI NeuroImage manuscript."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ── Colorblind-safe palette (Wong 2011) ──────────────────────────────────────
SUCCESS_C  = '#009E73'   # green
FAILURE_C  = '#D55E00'   # vermillion
NEVER_C    = '#999999'   # gray
READY_C    = '#0072B2'   # blue
RWL_C      = '#56B4E9'   # sky blue
RR_C       = '#E69F00'   # orange
HEATMAP_C  = 'YlOrRd'

FIG_W = 7.0
DPI   = 300
FONT  = 11

plt.rcParams.update({
    'font.size': FONT,
    'axes.labelsize': FONT,
    'axes.titlesize': FONT + 1,
    'xtick.labelsize': FONT - 1,
    'ytick.labelsize': FONT - 1,
    'legend.fontsize': FONT - 1,
    'figure.dpi': DPI,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'axes.grid.axis': 'y',
    'grid.alpha': 0.4,
})

def wilson_ci(n, N, z=1.96):
    """Wilson score 95% CI for proportion n/N."""
    if N == 0:
        return 0.0, 0.0, 0.0
    p = n / N
    denom = 1 + z**2 / N
    centre = (p + z**2 / (2*N)) / denom
    margin = (z * np.sqrt(p*(1-p)/N + z**2/(4*N**2))) / denom
    return p, max(0, centre - margin), min(1, centre + margin)


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — CIDUR readiness × QSIPrep outcome
# ════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(FIG_W * 0.65, 4.0))

labels    = ['ready\n(n=28)', 'ready_with_\nlimitations\n(n=41)', 'review_\nrequired\n(n=2)']
success   = np.array([26, 40, 0])
failure   = np.array([0,   1, 2])
no_out    = np.array([2,   0, 0])
totals    = success + failure + no_out
x = np.arange(len(labels))

b1 = ax.bar(x, success/totals*100, color=SUCCESS_C, label='QSIPrep success',  width=0.55)
b2 = ax.bar(x, failure/totals*100, bottom=success/totals*100, color=FAILURE_C,
            label='QSIPrep failure', width=0.55)
b3 = ax.bar(x, no_out/totals*100,  bottom=(success+failure)/totals*100, color=NEVER_C,
            label='No outcome available', width=0.55)

# Annotate counts
for i, (s, f, n, tot) in enumerate(zip(success, failure, no_out, totals)):
    if s: ax.text(i, s/tot*100/2, str(s), ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    if f: ax.text(i, s/tot*100 + f/tot*100/2, str(f), ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    if n: ax.text(i, (s+f)/tot*100 + n/tot*100/2, str(n), ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('Sessions (%)')
ax.set_ylim(0, 115)
ax.set_title('CIDUR cohort: Vecta readiness state versus QSIPrep outcome\n'
             '(n=71; in-sample development cohort)', pad=8)
ax.legend(loc='upper right', framealpha=0.9, ncol=1)
ax.text(0.5, -0.22, 'Failure rate: ready 0/26 (0%), ready_with_limitations 1/41 (2.4%), review_required 2/2 (100%)',
        transform=ax.transAxes, ha='center', fontsize=8.5, style='italic')

plt.tight_layout()
fig.savefig('figure_1_cidur_readiness_outcome.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Detection level comparison (CIDUR, n=69, 3 failures)
# ════════════════════════════════════════════════════════════════════════════
levels = ['Level 0\n(BIDS Validator)', 'Level 1\n(Metadata\ncompleteness)',
          'Level 2\n(Vecta Core)', 'Level 3\n(Vecta +\nDICOM)']

# Sensitivity
sens_p  = np.array([0.000, 0.667, 1.000, 1.000])
sens_lo = np.array([0.000, 0.208, 0.439, 0.439])
sens_hi = np.array([0.561, 0.939, 1.000, 1.000])

# NPV
npv_p   = np.array([0.957, 0.985, 1.000, 1.000])
npv_lo  = np.array([0.880, 0.920, 0.871, 0.871])
npv_hi  = np.array([0.985, 0.997, 1.000, 1.000])

x = np.arange(len(levels))
w = 0.35

fig, ax = plt.subplots(figsize=(FIG_W * 0.9, 4.5))

b1 = ax.bar(x - w/2, sens_p, w, color='#0072B2', label='Sensitivity', alpha=0.85)
b2 = ax.bar(x + w/2, npv_p,  w, color='#56B4E9', label='NPV',         alpha=0.85)

# CI error bars
sens_err = np.array([sens_p - sens_lo, sens_hi - sens_p])
npv_err  = np.array([npv_p  - npv_lo,  npv_hi  - npv_p])
ax.errorbar(x - w/2, sens_p, yerr=sens_err, fmt='none', color='#003057', capsize=4, lw=1.5)
ax.errorbar(x + w/2, npv_p,  yerr=npv_err,  fmt='none', color='#003057', capsize=4, lw=1.5)

ax.set_xticks(x)
ax.set_xticklabels(levels)
ax.set_ylabel('Value (95% Wilson CI)')
ax.set_ylim(0, 1.12)
ax.set_title('Detection level comparison versus QSIPrep failure\n'
             '(CIDUR, n=69, 3 failures — mechanistically illustrative; wide CIs)', pad=8)
ax.legend(framealpha=0.9)
ax.axhline(1.0, color='#333333', lw=0.8, ls='--', alpha=0.5)
ax.text(0.5, -0.23, 'Level 1 misses the eddy-stage failure (no fieldmap, valid PED/TRT). '
        'Level 2 captures both failure modes independently.',
        transform=ax.transAxes, ha='center', fontsize=8.5, style='italic')

plt.tight_layout()
fig.savefig('figure_2_detection_levels.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("Figure 2 saved.")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Cross-dataset criterion activation heatmap
# ════════════════════════════════════════════════════════════════════════════
criteria = [
    'VECTA-DWI-001\nPE dir. unknown',
    'VECTA-DWI-014\nCompl. PE ref. unavail.',
    'VECTA-DWI-021\nEssential metadata absent',
    'VECTA-DWI-030\nGradient file missing',
    'VECTA-DWI-031\nGradient norms implausible',
    'VECTA-DWI-040\nNo DWI present',
    'VECTA-DWI-050\nDICOM geometry incons.',
    'VECTA-DWI-060\nDICOM/BIDS FS disagree',
]
datasets = ['CIDUR\n(n=62)', 'TrackTBI\n(n=1,275)', 'SleepyBrain\n(n=76)',
            'MASiVar\n(n=281)', 'ON-Harmony\n(n=165)']

# Rows = criteria, cols = datasets; NaN = not evaluated
data = np.array([
    # CIDUR  TBI     SB     MASi  ONH
    [  0.0,  54.2,   0.0,   0.0,   0.0],  # 001
    [ 54.8,  45.8, 100.0,   0.0,   0.6],  # 014
    [  0.0,  54.2, 100.0, 100.0,   0.0],  # 021
    [  0.0,   0.0,   0.0,   1.8,   0.0],  # 030
    [  0.0,   0.0,   0.0,   0.0,   0.0],  # 031
    [  0.0,   0.0,   0.0,   0.0,   0.0],  # 040
    [  0.0,  np.nan, np.nan, np.nan, np.nan],  # 050
    [  0.0,  np.nan, np.nan, np.nan, np.nan],  # 060
])

fig, ax = plt.subplots(figsize=(FIG_W * 1.05, 5.2))
cmap = plt.get_cmap(HEATMAP_C).copy()
cmap.set_bad(color='#cccccc')

im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(datasets)))
ax.set_xticklabels(datasets, fontsize=9.5)
ax.set_yticks(range(len(criteria)))
ax.set_yticklabels(criteria, fontsize=8.5)

# Annotate cells
for i in range(len(criteria)):
    for j in range(len(datasets)):
        val = data[i, j]
        if np.isnan(val):
            ax.text(j, i, 'N/A', ha='center', va='center', fontsize=8, color='#666666')
        else:
            txt = f'{val:.0f}%' if val > 0 else '0%'
            color = 'white' if val > 55 else 'black'
            ax.text(j, i, txt, ha='center', va='center', fontsize=8, color=color, fontweight='bold' if val > 0 else 'normal')

cb = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
cb.set_label('Sessions triggered (%)', fontsize=9)
ax.set_title('Criterion activation rate across five datasets\n'
             '(gray = DICOM not available; criterion not evaluated)', pad=8)
ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
ax.xaxis.set_label_position('top')

plt.tight_layout()
fig.savefig('figure_3_criterion_heatmap.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("Figure 3 saved.")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — TrackTBI readiness × QSIPrep outcome (with CI on failure rate)
# ════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(FIG_W, 4.5), gridspec_kw={'width_ratios': [1.6, 1]})

# Left: stacked bar
ax = axes[0]
rwl_s, rwl_f, rwl_n = 444, 7,   133
rr_s,  rr_f,  rr_n  =   0, 620,  69
rwl_tot = rwl_s + rwl_f + rwl_n
rr_tot  = rr_s  + rr_f  + rr_n

labels = ['ready_with_\nlimitations\n(n=584)', 'review_\nrequired\n(n=689)']
x = np.array([0, 1])

succ = np.array([rwl_s / rwl_tot * 100, rr_s  / rr_tot  * 100])
fail = np.array([rwl_f / rwl_tot * 100, rr_f  / rr_tot  * 100])
nevr = np.array([rwl_n / rwl_tot * 100, rr_n  / rr_tot  * 100])

ax.bar(x, succ, color=SUCCESS_C, label='Success',         width=0.55)
ax.bar(x, fail, bottom=succ,     color=FAILURE_C, label='Failure',          width=0.55)
ax.bar(x, nevr, bottom=succ+fail,color=NEVER_C,  label='Never attempted',   width=0.55)

for i, (s, f, n, tot) in enumerate([(rwl_s, rwl_f, rwl_n, rwl_tot),
                                     (rr_s,  rr_f,  rr_n,  rr_tot)]):
    if s: ax.text(i, s/tot*100/2, str(s),   ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    if f: ax.text(i, s/tot*100 + f/tot*100/2, str(f), ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    if n: ax.text(i, (s+f)/tot*100 + n/tot*100/2, str(n), ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel('Sessions (%)')
ax.set_ylim(0, 115)
ax.set_title('TrackTBI (n=1,273 eligible)', pad=6)
ax.legend(loc='upper right', framealpha=0.9, fontsize=8.5)

# Right: failure rate with Wilson CI
ax2 = axes[1]
fail_rates = [rwl_f / (rwl_s + rwl_f), rr_f / (rr_s + rr_f)]
_, rwl_lo, rwl_hi = wilson_ci(rwl_f, rwl_s + rwl_f)
_, rr_lo,  rr_hi  = wilson_ci(rr_f,  rr_s  + rr_f)
fr_lo = [rwl_lo, rr_lo]
fr_hi = [rwl_hi, rr_hi]
errs  = np.array([[max(0, fr - lo), max(0, hi - fr)] for fr, lo, hi in zip(fail_rates, fr_lo, fr_hi)]).T

colors = [RWL_C, RR_C]
ax2.barh(x, fail_rates, color=colors, height=0.45)
ax2.errorbar(fail_rates, x, xerr=errs, fmt='none', ecolor='#333333', capsize=4, lw=1.5)
ax2.set_yticks(x)
ax2.set_yticklabels(['ready_with_\nlimitations', 'review_\nrequired'])
ax2.set_xlabel('QSIPrep failure rate')
ax2.set_xlim(0, 1.12)
ax2.set_title('Failure rate\n(95% Wilson CI)', pad=6)
for i, (r, lo, hi) in enumerate(zip(fail_rates, fr_lo, fr_hi)):
    ax2.text(r + 0.04, i, f'{r:.1%}\n[{lo:.3f},{hi:.3f}]', va='center', fontsize=8)

plt.suptitle('TrackTBI: Vecta-DWI readiness state versus QSIPrep outcome\n'
             '(n=1,071 confirmed outcomes; 202 never attempted excluded)', y=1.01, fontsize=FONT)
plt.tight_layout()
fig.savefig('figure_4_tracktbi_readiness_outcome.png', dpi=DPI, bbox_inches='tight')
plt.close()
print("Figure 4 saved.")

print("\nAll figures generated successfully.")
