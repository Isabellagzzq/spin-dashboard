# Spin dashboard: who should Marketing nudge next?

This dashboard helps the Marketing team at Spin decide which users to nudge first with a non-OXXO purchase incentive,
given that Marketing can only reach a limited share of the base each month.

## Run
```
pip install -r requirements.txt
streamlit run app.py
```
Keep the `data` folder next to `app.py`.

## Pages
1. Who our users are: KPIs, persona share, descriptive statistics, definitions, PCA and clustering quality.
2. Who flips: how Flip-Out / Flip-In are defined, flippers vs non-flippers side by side by month, biggest differences.
3. Personas: one card per persona with suggested action, radar and side-by-side heatmap.
4. Target list: users ranked by score, persona and decile filters, capacity slider (5-30%) vs random contact.
5. The model: version, PR-AUC, capture at 10%, model comparison, top drivers, decision-tree rules, what changed.

Filters at the top (behavior, months, persona) change every chart.

## Privacy
Only aggregated tables and anonymous user keys are in `data/`. No raw Spin data.
