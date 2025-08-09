# Backtest Report (Individual Asset Focus) for XLU

## Backtest Configuration
- **Universe:** This asset ONLY.
- **Starting Capital:** `$100,000.00`
- **Position Sizing:** Each trade uses **100%** of available equity (compounding).
- **Strategy:** Buy on Close crossing above the **52-period SMA**.
- **Stop Loss Mode:** `PREVIOUS_YEAR_LOW`
- **Analysis Period:** 1999-03-09 to 2025-08-06 (26.4 years)

## Performance Summary
_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._

| Metric                  | Strategy (Optimal) | Buy & Hold |
|:------------------------|:-------------------|:-----------|
| **Optimal Combination**     | SL: `N/A`, PT: `150` | N/A        |
| **Final P&L ($)**           | `$3,720,846.41`         | `$652,977.54`  |
| **CAGR (%)**              | `14.82`%                | `$7.96`%     |
| **Max Drawdown (%)**      | `38.78`%           | `$52.27`%|
| **Calmar Ratio**          | `0.38`                  | `0.15`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)      |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-------------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 2,026,623.12 |      12.29 |              46.48 |           0.26 |             13 |          53.85 |
| N/A              | 50                  | 2,398,073.57 |      12.98 |              38.81 |           0.33 |             27 |          66.67 |
| N/A              | 100                 | 2,713,074.24 |      13.49 |              47.41 |           0.28 |             24 |          62.5  |
| N/A              | 150                 | 3,720,846.41 |      14.82 |              38.78 |           0.38 |             22 |          63.64 |
| N/A              | 200                 | 2,021,023.36 |      12.28 |              46.48 |           0.26 |             15 |          60    |