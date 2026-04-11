# Phase 6 Dashboard (Localhost)

## What this is
A lightweight Streamlit dashboard for teammate demos using existing Phase 5 outputs.

## Data source
- `output/phase5_executive_recommendations.csv`

## Run steps (Windows PowerShell)
1. Activate environment:
   - `& .\d_env\Scripts\Activate.ps1`
2. Install dependencies (first time only):
   - `pip install -r requirements.txt`
3. Start dashboard:
   - `streamlit run app.py`
4. Open browser:
   - Streamlit prints a localhost URL (usually `http://localhost:8501`)

## Included views
- Executive KPIs
- Segment and elasticity charts
- Search/filter store performance table
- CSV export of filtered rows
- Session-only implementation status tracker

## Notes
- This is intentionally simple and localhost-only.
- Implementation status edits are not persisted to disk.
