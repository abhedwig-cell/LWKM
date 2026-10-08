# W07 S/T merge heterogeneity versus HRU relief — 2026-10-08

Status: POPULATION DIAGNOSTIC; NOT PRODUCTION ADMISSION.

Sources: recovered Q4 W07 `ahn_f250_cm.asc`, 427656-member relation, corrected `st_candidate.csv`, and seven-system activity preflight. Relief is max(AHN)-min(AHN) across members in each HRU. S/T tension is the maximum of summer/winter drainage-versus-infiltration equivalent-level gap, in metres.

Results: 8962 HRUs with S and T active; Spearman rho(relief,gap)=0.7243. In 5908 S/T-active HRUs requiring compression, rho=0.6986. Among 116 S/T-active HRUs with gap >1 m, 113 have relief >5 m and 107 have relief >10 m.

Compression-population p95 gap by relief bin: <=1 m: 0.000664 m (454 HRUs); 1–2 m: 0.003916 m (931); 2–5 m: 0.017234 m (1464); 5–10 m: 0.183258 m (1110); 10–20 m: 0.271366 m (1184); >20 m: 0.464637 m (511).

Outlier examples (HRU, relief m, centroid gap m, active systems): (1736,160.319,19.652,4), (1883,115.565,15.695,4), (1828,27.721,10.680,4), (1778,137.074,10.147,4), (1713,86.634,8.705,4), (4261,73.622,8.358,5).

Interpretation: relief strongly associates with S/T tension but does not establish causality. Relief alone cannot replace direct hydraulic error guard. Protected H1 and PIPE, preferred MVG+OLF, conditional S+T remain candidate policy only. HRUs with <=5 active systems should not merge at all. A candidate relief screening threshold around 5 m warrants sensitivity analysis, not automatic admission.

Reproducibility: diagnostic computed from actual member x/y raster sampling and corrected S/T candidate CSV. No dqsat is needed for this association test.