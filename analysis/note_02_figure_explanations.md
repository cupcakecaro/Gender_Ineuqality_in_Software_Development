# Figure Explanations and Conclusions (Figures 01-05)

## Scope and Reminder
- Population: women-only profiles (already pre-selected in the dataset).
- Country focus: Sweden and Romania.
- Strict LCNC vs Traditional comparison excludes Mixed and Other in survival/Cox models.
- Outcome A: first observed role with seniority >= 4.
- Outcome B: first observed role with seniority >= 5.

## Figure 01: Kaplan-Meier for Outcome A
File: analysis/plots/figure_01_km_outcome_a_by_country.png

Why this plot is used:
- Kaplan-Meier curves show how quickly groups reach the milestone while correctly handling censored careers.
- The y-axis is the probability of NOT yet reaching Outcome A.

How to read it:
- A faster downward curve means faster progression.
- Compare LCNC vs Traditional within each country panel.

Conclusion:
- Sweden: LCNC and Traditional are fairly close for much of the trajectory, with LCNC slightly ahead by later horizons.
- Romania: LCNC is also slightly ahead, but differences are modest.
- Overall from the curve shape: evidence points to a possible LCNC advantage for Outcome A, but not a strong separation.

## Figure 02: Kaplan-Meier for Outcome B
File: analysis/plots/figure_02_km_outcome_b_by_country.png

Why this plot is used:
- Same survival logic as Figure 01, but for the higher progression threshold.

How to read it:
- Lower survival probability means more profiles already reached seniority >= 5.

Conclusion:
- Sweden: LCNC reaches Outcome B faster than Traditional, especially by later months.
- Romania: LCNC also tends to be faster than Traditional.
- Visual pattern suggests stronger LCNC advantage for Outcome B than for Outcome A.

## Figure 03: Cumulative Incidence Heatmaps
File: analysis/plots/figure_03_cumulative_incidence_heatmaps.png
Data table: analysis/table_02_cumulative_incidence_sweden_romania.csv

Why this plot is used:
- Gives exact percentages at practical checkpoints (12, 24, 36, 60 months), which is easier to report in text than reading curves.

How to read it:
- Darker colors and larger numbers indicate higher share reaching milestone by that time.

Key values and conclusion:
- Sweden Outcome A at 60 months:
  - Traditional: 0.47
  - LCNC: 0.55
  - Conclusion: LCNC higher by 8 percentage points.
- Sweden Outcome B at 60 months:
  - Traditional: 0.25
  - LCNC: 0.45
  - Conclusion: LCNC higher by 20 percentage points.
- Romania Outcome A at 60 months:
  - Traditional: 0.24
  - LCNC: 0.25
  - Conclusion: nearly equal, slight LCNC advantage.
- Romania Outcome B at 60 months:
  - Traditional: 0.12
  - LCNC: 0.20
  - Conclusion: LCNC higher by 8 percentage points.

Overall takeaway from Figure 03:
- Sweden shows the clearest LCNC advantage, especially for Outcome B.
- Romania also shows LCNC advantage, but smaller in absolute size.

## Figure 04: Cox Hazard-Ratio Forest Plot
File: analysis/plots/figure_04_cox_forest_key_terms.png
Data tables:
- analysis/table_03_cox_summary_outcome_a.csv
- analysis/table_04_cox_summary_outcome_b.csv

Why this plot is used:
- Cox models estimate adjusted progression speed (hazard ratios), controlling for baseline seniority, number of roles, and career start year.
- The interaction term tests if the LCNC effect differs in Romania vs Sweden.

How to read it:
- HR > 1 means faster progression.
- If confidence interval crosses 1, the effect is not statistically conclusive.

Key estimates and conclusion:
- Outcome A, LCNC main effect: HR = 1.14 (95% CI 0.70-1.84).
- Outcome B, LCNC main effect: HR = 1.55 (95% CI 0.88-2.74).
- LCNC x Romania interaction:
  - Outcome A: HR = 1.17 (95% CI 0.52-2.63)
  - Outcome B: HR = 1.67 (95% CI 0.63-4.46)
- Interpretation:
  - Direction is LCNC-positive in both outcomes.
  - But CIs cross 1 for LCNC and interaction terms, so results are suggestive, not statistically definitive.

Additional robust signals from Cox tables:
- Baseline seniority and number of roles are strong positive predictors in both outcomes.

## Figure 05: Trajectory Endpoint Heatmap (All Profiles)
File: analysis/plots/figure_05_trajectory_endpoint_heatmap_all_profiles.png
Data table: analysis/table_05_trajectory_endpoints_all_profiles.csv

Why this plot is used:
- This is the broad career-mobility view that includes all profile types and endpoint role labels, including Other.
- Useful for your question about transitions like developer to executive roles that may be classified as Other.

How to read it:
- Rows: initial profile type.
- Columns: endpoint role label at highest observed seniority.
- Cell values: number of profiles.

Conclusion:
- Traditional profiles often end in Traditional labels (119), but many also end in Other (63), showing substantial movement beyond core dev labels.
- LCNC profiles split between LCNC endpoints (33) and Other endpoints (38), indicating broad progression paths including non-core role labels.
- Mixed profiles also distribute across all endpoint labels.
- This confirms that broader endpoint categories (including Other) carry important career-progression information and should be analyzed separately, as planned.

## Overall Conclusion Across Figures 01-05
- Directionally, LCNC profiles tend to progress faster than Traditional profiles for both thresholds, with strongest practical differences in Sweden and for Outcome B.
- Romania shows similar direction but smaller absolute differences.
- Cox model uncertainty is still high (wide CIs crossing 1 for LCNC and interaction), so current evidence should be reported as suggestive rather than definitive.
- The all-profile trajectory view shows that endpoint roles labeled Other are meaningful career outcomes, not noise, and should be included in dedicated secondary analyses.

## Suggested Thesis Wording (Short Version)
"Across Sweden and Romania, women in LCNC profiles show a directionally faster progression pattern than women in traditional software-development profiles, especially for reaching seniority >= 5 in Sweden. However, adjusted hazard-ratio confidence intervals include the null value, so findings should be interpreted as suggestive rather than conclusive. A broader trajectory analysis further indicates that many careers end in roles classified as 'Other', implying that non-core role transitions are an important part of progression pathways and warrant separate analysis."

## Additional Finding: PH Diagnostics (from note_03)
Data references:
- analysis/table_06_ph_assumptions_test.csv
- analysis/table_07_robust_cox_stratified.csv

Why this matters:
- Cox interpretation assumes proportional hazards over time. Violations mean some effects are time-varying.

Key diagnostic result:
- baseline_seniority violates PH in both outcomes.
- Outcome A also shows a borderline country-effect PH issue (is_romania).
- LCNC terms do not show clear PH violation in this check.

PH-aware robustness conclusion:
- After stratifying by baseline seniority bins, LCNC effect is not statistically conclusive:
  - Outcome A pooled stratified: HR = 0.86 (95% CI 0.53-1.40, p = 0.544)
  - Outcome B pooled stratified: HR = 1.10 (95% CI 0.62-1.97, p = 0.744)
- Romania interaction remains non-significant in pooled stratified models.

Interpretation for thesis:
- Directional patterns remain informative, but PH-aware models support cautious interpretation (suggestive, not definitive).

## Additional Finding: Mixed Group as Dedicated Category (from note_04)
Data references:
- analysis/table_08_mixed_group_cumulative_incidence.csv
- analysis/table_09_cox_three_group_stratified.csv
- analysis/plots/figure_06_km_outcome_a_with_mixed.png
- analysis/plots/figure_07_km_outcome_b_with_mixed.png
- analysis/plots/figure_08_mixed_group_cumulative_incidence_heatmaps.png

Why this matters:
- Mixed profiles are substantively meaningful and should not be forced into LCNC/Traditional in the main comparison.

Key model result (Traditional as reference, baseline-stratified Cox):
- Outcome A:
  - LCNC vs Traditional: HR = 0.87 (95% CI 0.53-1.41, p = 0.560)
  - Mixed vs Traditional: HR = 0.31 (95% CI 0.12-0.78, p = 0.013)
- Outcome B:
  - LCNC vs Traditional: HR = 1.11 (95% CI 0.62-1.99, p = 0.713)
  - Mixed vs Traditional: HR = 0.49 (95% CI 0.17-1.43, p = 0.193)

Interpretation for thesis:
- Mixed profiles show distinctly slower progression for Outcome A in this sample.
- For Outcome B, Mixed is still below 1 in direction but not conclusive.
- This supports treating Mixed as a separate analytical group in secondary analyses.

## Additional Finding: Threshold Sensitivity (from note_05)
Data references:
- analysis/table_10_threshold_sensitivity_cox.csv
- analysis/note_05_threshold_sensitivity.txt

Why this matters:
- Conclusions can depend on where the progression threshold is set.

Key result (baseline-stratified strict sample):
- Threshold >= 4: LCNC HR = 0.86 (95% CI 0.53-1.40, p = 0.544)
- Threshold >= 5: LCNC HR = 1.10 (95% CI 0.62-1.97, p = 0.744)
- Threshold >= 6: LCNC HR = 1.41 (95% CI 0.73-2.73, p = 0.307)

Interpretation for thesis:
- Direction changes from slight disadvantage at lower threshold to advantage at stricter thresholds.
- None of the threshold-specific LCNC effects are statistically conclusive.
- Report threshold dependence explicitly as a robustness caveat.

## Consolidated Bottom Line
- Descriptive plots suggest LCNC may be associated with faster progression, especially at higher progression thresholds and in Sweden.
- PH-aware and threshold-robust Cox analyses reduce certainty: LCNC effects remain directionally interesting but statistically non-conclusive in this sample.
- Mixed profiles behave differently and should be handled as a separate group rather than merged with LCNC/Traditional.

## Additional Finding: Country-Stratified Decomposition (from note_06)
Data references:
- analysis/table_11_country_stratified_lcnc_effects.csv
- analysis/plots/figure_09_country_stratified_lcnc_forest.png
- analysis/note_06_country_stratified_decomposition.txt

Why this matters:
- This directly estimates LCNC vs Traditional effects within each country instead of relying only on pooled interaction terms.

Key result (baseline-seniority stratified country-specific Cox):
- Outcome A (>=4):
  - Sweden: HR = 0.94 (95% CI 0.57-1.53, p = 0.791)
  - Romania: HR = 1.09 (95% CI 0.55-2.17, p = 0.805)
- Outcome B (>=5):
  - Sweden: HR = 1.23 (95% CI 0.68-2.22, p = 0.485)
  - Romania: HR = 1.54 (95% CI 0.65-3.64, p = 0.322)

Interpretation for thesis:
- Outcome A shows different direction by country (slightly below 1 in Sweden, above 1 in Romania), but both are highly uncertain.
- Outcome B is directionally LCNC-positive in both countries and stronger in Romania, but still statistically non-conclusive.
- This supports a cautious heterogeneity narrative: country context may matter, but current sample precision is limited.

## Additional Finding: Cohort / Time-Period Check (from note_07)
Data references:
- analysis/table_12_cohort_timeperiod_effects.csv
- analysis/plots/figure_10_cohort_timeperiod_lcnc_effects.png
- analysis/note_07_cohort_timeperiod_check.txt

Why this matters:
- It checks whether LCNC effects are stable across career-entry periods or mainly driven by a specific cohort.

Key result (baseline-seniority stratified, strict LCNC vs Traditional):
- Outcome A (>=4):
  - cohort <=2009: HR = 1.25 (95% CI 0.56-2.80, p = 0.592)
  - cohort 2010-2016: HR = 0.92 (95% CI 0.54-1.58, p = 0.770)
  - cohort >=2017: HR = 0.79 (95% CI 0.32-1.98, p = 0.620)
- Outcome B (>=5):
  - cohort <=2009: HR = 1.53 (95% CI 0.63-3.69, p = 0.349)
  - cohort 2010-2016: HR = 1.37 (95% CI 0.71-2.63, p = 0.346)
  - cohort >=2017: HR = 0.75 (95% CI 0.21-2.73, p = 0.662)

Interpretation for thesis:
- LCNC direction varies by cohort, especially for newer careers (>=2017), where direction can reverse.
- None of the cohort-specific effects are statistically conclusive.
- This suggests possible period dependency, but with current sample size the cohort heterogeneity should be reported as exploratory.

## Additional Finding: Bootstrap Uncertainty Intervals (from note_08)
Data references:
- analysis/table_13_bootstrap_uncertainty.csv
- analysis/plots/figure_11_bootstrap_uncertainty_intervals.png
- analysis/note_08_bootstrap_uncertainty.txt

Why this matters:
- Bootstrap intervals provide a distribution-based uncertainty check for the key practical contrasts and the pooled LCNC hazard-ratio estimates.

Key result (300 percentile bootstrap resamples):
- 60-month cumulative-incidence gap (LCNC - Traditional):
  - Sweden Outcome A (>=4): +0.078, 95% CI [-0.113, 0.305]
  - Sweden Outcome B (>=5): +0.207, 95% CI [0.004, 0.417]
  - Romania Outcome A (>=4): +0.012, 95% CI [-0.133, 0.171]
  - Romania Outcome B (>=5): +0.081, 95% CI [-0.045, 0.216]
- Pooled baseline-stratified Cox LCNC hazard ratio:
  - Outcome A (>=4): HR = 0.860, 95% CI [0.515, 1.267]
  - Outcome B (>=5): HR = 1.101, 95% CI [0.631, 1.986]

Interpretation for thesis:
- Most uncertainty intervals include the null (0 for gaps, 1 for HR), so effects remain statistically inconclusive.
- The strongest signal is Sweden Outcome B, where the 60-month LCNC advantage remains positive with a CI barely above 0.
- Overall, bootstrap results reinforce the same conclusion as prior robustness checks: directionally interesting LCNC patterns, but limited precision and thus suggestive rather than definitive evidence.

## Additional Finding: Standardized 60-Month Effects (from note_09)
Data references:
- analysis/table_14_standardized_60m_effects.csv
- analysis/plots/figure_12_standardized_60m_effects.png
- analysis/note_09_standardized_60m_effects.txt

Why this matters:
- This is a model-light sensitivity check focused on practical 60-month progression probability differences, standardized across baseline seniority and cohort strata.

Key result (180 percentile bootstrap resamples):
- Pooled (Sweden + Romania):
  - Outcome A (>=4): RD = +0.008, 95% CI [-0.123, 0.123]
  - Outcome B (>=5): RD = +0.071, 95% CI [-0.030, 0.177]
- Sweden:
  - Outcome A (>=4): RD = -0.009, 95% CI [-0.211, 0.221]
  - Outcome B (>=5): RD = +0.061, 95% CI [-0.106, 0.210]
- Romania:
  - Outcome A (>=4): RD = +0.026, 95% CI [-0.137, 0.211]
  - Outcome B (>=5): RD = +0.081, 95% CI [-0.077, 0.245]

Interpretation for thesis:
- Signs are mostly LCNC-positive (especially Outcome B), but all intervals include 0.
- This aligns with the Cox/PH/bootstrap narrative: directional LCNC advantage in several specifications, but uncertainty remains high.
- As a complementary check, this supports reporting practical effect sizes together with uncertainty rather than relying on a single model family.

## Additional Finding: Informative-Censoring Sensitivity (from note_10)
Data references:
- analysis/table_15_followup_window_sensitivity.csv
- analysis/plots/figure_13_followup_window_sensitivity.png
- analysis/note_10_followup_window_sensitivity.txt

Why this matters:
- If LCNC effects change strongly when requiring longer observed follow-up, conclusions may be driven by follow-up-related censoring.

Key result (pooled baseline-stratified Cox across follow-up windows):
- Outcome A (>=4):
  - min follow-up 0m: HR = 0.911 (95% CI 0.618-1.344)
  - min follow-up 36m: HR = 0.887 (95% CI 0.599-1.313)
  - min follow-up 60m: HR = 0.868 (95% CI 0.576-1.307)
- Outcome B (>=5):
  - min follow-up 0m: HR = 1.235 (95% CI 0.774-1.970)
  - min follow-up 36m: HR = 1.187 (95% CI 0.739-1.906)
  - min follow-up 60m: HR = 1.244 (95% CI 0.764-2.025)

Interpretation for thesis:
- LCNC effect direction remains stable as follow-up requirements tighten: below 1 for Outcome A and above 1 for Outcome B.
- Magnitude shifts are small and confidence intervals overlap strongly across windows.
- This suggests limited additional evidence for severe informative-censoring bias in the current sample, while overall statistical uncertainty remains substantial.

## Additional Finding: Final Cross-Model Synthesis (from note_11)
Data references:
- analysis/table_16_final_synthesis_summary.csv
- analysis/note_11_final_synthesis_summary.txt

Why this matters:
- This consolidates all major LCNC-vs-Traditional estimates from the full analysis pipeline into one thesis-ready summary table with aligned conclusion tags.

Key synthesis counts:
- Total synthesized estimates: 35
- CI-conclusive estimates (CI excludes null): 1
- CI-uncertain estimates (CI includes null): 34

Directional pattern (not significance-weighted):
- Outcome A-related estimates: LCNC-positive = 7, LCNC-negative = 10
- Outcome B-related estimates: LCNC-positive = 16, LCNC-negative = 1

Interpretation for thesis:
- Across the full specification set, most estimates remain uncertainty-dominated (CIs crossing null), reinforcing a suggestive rather than definitive claim.
- Outcome B shows a consistently more LCNC-positive directional pattern across methods.
- Outcome A is more mixed and specification-sensitive.
- The synthesis table provides a transparent audit trail from each robustness block to the final substantive interpretation.

## Figure Pack Export (Thesis-Ready)
Data references:
- analysis/figure_pack_index.md
- analysis/figure_pack/

What was standardized:
- Unified export canvas for all figures: 2400x1600 px.
- White background with centered figure content and consistent margins.
- PNG export at 300 DPI for thesis insertion.

Result:
- A cleaned figure bundle with 13 standardized files is available in `analysis/figure_pack/`.
- A single lookup index with purpose and source mapping is available in `analysis/figure_pack_index.md`.

Interpretation for workflow:
- This export pass harmonizes presentation quality across all analysis figures without changing statistical content.
- The index file can be used as the figure manifest when integrating plots into the thesis chapters.