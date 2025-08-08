# Backtest Report (Individual Asset Focus) for XLV

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
| **Optimal Combination**     | SL: `N/A`, PT: `None` | N/A        |
| **Final P&L ($)**           | `$445,579.00`         | `$589,830.70`  |
| **CAGR (%)**              | `6.65`%                | `$7.60`%     |
| **Max Drawdown (%)**      | `45.58`%           | `$39.17`%|
| **Calmar Ratio**          | `0.15`                  | `0.19`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)    |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-----------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 445,579.00 |       6.65 |              45.58 |           0.15 |              4 |          50    |
| N/A              | 50                  | 376,369.99 |       6.1  |              45.58 |           0.13 |             10 |          70    |
| N/A              | 100                 | 437,099.92 |       6.58 |              45.58 |           0.14 |              7 |          57.14 |
| N/A              | 150                 | 407,932.42 |       6.36 |              45.58 |           0.14 |              6 |          66.67 |
| N/A              | 200                 | 415,573.88 |       6.42 |              45.58 |           0.14 |              5 |          60    |