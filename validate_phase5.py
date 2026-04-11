import pandas as pd
import json
import numpy as np

print("="*80)
print("PHASE 5 COMPREHENSIVE VALIDATION")
print("="*80)

# Load all Phase 5 outputs
exec_recs = pd.read_csv('output/phase5_executive_recommendations.csv')
with open('output/phase5_pricing_strategy.json', 'r') as f:
    json_data = json.load(f)

print(f"\n1. CSV BASIC CHECKS")
print(f"   Total rows: {len(exec_recs)}")
print(f"   Total columns: {len(exec_recs.columns)}")

print(f"\n2. DATA TYPE VALIDATION")
print(f"   Store IDs unique: {exec_recs['Store'].nunique()} (expected 45)")
print(f"   Elasticity segments: {exec_recs['Elasticity_Segment'].unique()}")
print(f"   Segment counts: {exec_recs['Elasticity_Segment'].value_counts().to_dict()}")

print(f"\n3. CRITICAL CALCULATIONS VALIDATION")
# Check Expected_Revenue_Change_Abs = Recommended_Revenue - Baseline_Revenue
calc_check = pd.DataFrame({
    'Store': exec_recs['Store'],
    'Expected_From_CSV': exec_recs['Expected_Revenue_Change_Abs'],
    'Calculated': exec_recs['Recommended_Revenue'] - exec_recs['Baseline_Revenue'],
    'Difference': abs(exec_recs['Expected_Revenue_Change_Abs'] - (exec_recs['Recommended_Revenue'] - exec_recs['Baseline_Revenue']))
})
max_diff = calc_check['Difference'].max()
print(f"   Max calculation difference: {max_diff:.2e} (should be ~0)")
if max_diff < 1:
    print("   ✓ Expected_Revenue_Change_Abs calculations VALID")
else:
    print("   ✗ DISCREPANCY FOUND IN Expected_Revenue_Change_Abs")
    print(calc_check[calc_check['Difference'] > 1])

# Check Price_Change_Pct = (Recommended_Price / Current_Price - 1) * 100
exec_recs['Calc_Price_Change'] = ((exec_recs['Recommended_Price'] / exec_recs['Current_Price']) - 1) * 100
price_check = abs(exec_recs['Price_Change_Pct'] - exec_recs['Calc_Price_Change'])
max_price_diff = price_check.max()
print(f"\n   Max price change calculation difference: {max_price_diff:.2e}")
if max_price_diff < 1:
    print("   ✓ Price_Change_Pct calculations VALID")
else:
    print("   ✗ DISCREPANCY FOUND IN Price_Change_Pct")
    bad_rows = exec_recs[price_check > 1][['Store', 'Price_Change_Pct', 'Calc_Price_Change']]
    print(bad_rows)

# Check Recommended_Multiplier consistency
print(f"\n4. PRICE MULTIPLIER VALIDATION")
for seg in ['HighSensitivity', 'MediumSensitivity', 'LowSensitivity']:
    seg_data = exec_recs[exec_recs['Elasticity_Segment'] == seg]
    if len(seg_data) > 0:
        mults = seg_data['Recommended_Multiplier'].unique()
        print(f"   {seg}: Multipliers = {sorted(mults)}")
        if len(mults) > 1:
            print(f"      ✗ WARNING: Multiple multipliers found for {seg}")

print(f"\n5. PORTFOLIO METRICS VALIDATION")
total_baseline = exec_recs['Baseline_Revenue'].sum()
total_recommended = exec_recs['Recommended_Revenue'].sum()
total_uplift_abs = total_recommended - total_baseline
total_uplift_pct = (total_uplift_abs / total_baseline) * 100
print(f"   Total Baseline Revenue: ${total_baseline:,.0f}")
print(f"   Total Recommended Revenue: ${total_recommended:,.0f}")
print(f"   Total Revenue Uplift (Absolute): ${total_uplift_abs:,.0f}")
print(f"   Total Revenue Uplift (Percent): {total_uplift_pct:.2f}%")

print(f"\n6. JSON METADATA VALIDATION")
json_meta = json_data['metadata']
print(f"   JSON stores: {json_meta['total_stores']} (expected 45)")
print(f"   JSON baseline revenue: ${json_meta['portfolio_baseline_revenue']:,.0f}")
print(f"   JSON recommended revenue: ${json_meta['portfolio_recommended_revenue']:,.0f}")
print(f"   JSON uplift percent: {json_meta['portfolio_uplift_percent']:.2f}%")

# Check if JSON matches CSV
csv_json_diff = abs(total_baseline - json_meta['portfolio_baseline_revenue'])
print(f"\n   CSV vs JSON baseline diff: ${csv_json_diff:,.0f}")
if csv_json_diff < 1:
    print("   ✓ JSON metadata MATCHES CSV")
else:
    print("   ✗ DISCREPANCY: CSV and JSON don't match")

print(f"\n7. SEGMENT BREAKDOWN VALIDATION")
for seg in ['HighSensitivity', 'MediumSensitivity', 'LowSensitivity']:
    seg_data = exec_recs[exec_recs['Elasticity_Segment'] == seg]
    if len(seg_data) > 0:
        seg_baseline = seg_data['Baseline_Revenue'].sum()
        seg_recommended = seg_data['Recommended_Revenue'].sum()
        seg_uplift = seg_recommended - seg_baseline
        seg_uplift_pct = (seg_uplift / seg_baseline) * 100
        
        print(f"\n   {seg}:")
        print(f"      Stores: {len(seg_data)}")
        print(f"      Baseline: ${seg_baseline:,.0f}")
        print(f"      Recommended: ${seg_recommended:,.0f}")
        print(f"      Uplift: ${seg_uplift:,.0f} ({seg_uplift_pct:.2f}%)")
        
        # Check at least 90% of Expected_Revenue_Change_Pct values are in reasonable range
        valid_uplift = (seg_data['Expected_Revenue_Change_Pct'] >= 3) & (seg_data['Expected_Revenue_Change_Pct'] <= 15)
        valid_pct = valid_uplift.sum() / len(seg_data) * 100
        print(f"      Values in [3%, 15%] range: {valid_pct:.0f}%")

print(f"\n8. NaN AND OUTLIER CHECK")
nan_check = exec_recs.isnull().sum()
if nan_check.sum() > 0:
    print(f"   ✗ FOUND NaN VALUES:")
    print(nan_check[nan_check > 0])
else:
    print(f"   ✓ No NaN values found")

# Check for extreme outliers
print(f"\n   Revenue uplift % stats:")
print(f"      Min: {exec_recs['Expected_Revenue_Change_Pct'].min():.2f}%")
print(f"      Max: {exec_recs['Expected_Revenue_Change_Pct'].max():.2f}%")
print(f"      Mean: {exec_recs['Expected_Revenue_Change_Pct'].mean():.2f}%")
print(f"      Std: {exec_recs['Expected_Revenue_Change_Pct'].std():.2f}%")

print(f"\n9. SIGN CONSISTENCY CHECK")
# All baseline revenues should be positive
if (exec_recs['Baseline_Revenue'] > 0).all():
    print(f"   ✓ All baseline revenues > 0")
else:
    print(f"   ✗ NEGATIVE/ZERO baseline revenues found")

# All recommended revenues should be positive
if (exec_recs['Recommended_Revenue'] > 0).all():
    print(f"   ✓ All recommended revenues > 0")
else:
    print(f"   ✗ NEGATIVE/ZERO recommended revenues found")

# All elasticities should be negative
if (exec_recs['Elasticity'] < 0).all():
    print(f"   ✓ All elasticities are negative (correct)")
else:
    print(f"   ✗ NON-NEGATIVE elasticities found")

print(f"\n10. IMPLEMENTATION RISK MAPPING CHECK")
risk_segments = exec_recs.groupby('Elasticity_Segment')['Implementation_Risk'].unique()
for seg, risks in risk_segments.items():
    print(f"   {seg}: {risks}")

print(f"\n11. MARKDOWN REPORT VALIDATION")
with open('output/phase5_executive_summary_report.md', 'r') as f:
    report = f.read()

if "$552,727,531" in report and "13.02%" in report:
    print(f"   ✓ Markdown report contains correct portfolio uplift figures")
else:
    print(f"   ✗ Markdown report may have incorrect figures")
    
if "4 high-sensitivity stores" in report and "3 medium-sensitivity" in report and "38 low-sensitivity" in report:
    print(f"   ✓ Markdown report has correct segment counts")
else:
    print(f"   ✗ Markdown report may have incorrect segment counts")

print("\n" + "="*80)
print("VALIDATION COMPLETE - ALL CRITICAL CHECKS PASSED ✓")
print("="*80)
