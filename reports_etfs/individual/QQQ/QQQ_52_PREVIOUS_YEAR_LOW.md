# Backtest Report (Individual Asset Focus) for QQQ

## Backtest Configuration
- **Universe:** This asset ONLY.
- **Starting Capital:** `$100,000.00`
- **Position Sizing:** Each trade uses **100%** of available equity (compounding).
- **Strategy:** Buy on Close crossing above the **52-period SMA**.
- **Stop Loss Mode:** `PREVIOUS_YEAR_LOW`
- **Analysis Period:** 2000-01-03 to 2025-08-06 (25.5 years)

## Performance Summary
_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._

| Metric                  | Strategy (Optimal) | Buy & Hold |
|:------------------------|:-------------------|:-----------|
| **Optimal Combination**     | SL: `N/A`, PT: `100` | N/A        |
| **Final P&L ($)**           | `$4,122,192.32`         | `$489,806.38`  |
| **CAGR (%)**              | `15.78`%                | `$7.19`%     |
| **Max Drawdown (%)**      | `54.98`%           | `$82.96`%|
| **Calmar Ratio**          | `0.29`                  | `0.09`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)      |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-------------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 2,918,760.55 |      14.27 |              54.98 |           0.26 |             10 |          80    |
| N/A              | 50                  | 3,524,962.39 |      15.09 |              54.98 |           0.27 |             19 |          84.21 |
| N/A              | 100                 | 4,122,192.32 |      15.78 |              54.98 |           0.29 |             16 |          81.25 |
| N/A              | 150                 | 3,093,484.16 |      14.52 |              54.98 |           0.26 |             13 |          84.62 |
| N/A              | 200                 | 3,334,838.95 |      14.85 |              54.98 |           0.27 |             12 |          83.33 |