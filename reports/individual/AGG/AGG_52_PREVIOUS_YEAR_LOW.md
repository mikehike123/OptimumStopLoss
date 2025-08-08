# Backtest Report (Individual Asset Focus) for AGG

## Backtest Configuration
- **Universe:** This asset ONLY.
- **Starting Capital:** `$100,000.00`
- **Position Sizing:** Each trade uses **100%** of available equity (compounding).
- **Strategy:** Buy on Close crossing above the **52-period SMA**.
- **Stop Loss Mode:** `PREVIOUS_YEAR_LOW`
- **Analysis Period:** 2004-01-02 to 2025-08-06 (21.6 years)

## Performance Summary
_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._

| Metric                  | Strategy (Optimal) | Buy & Hold |
|:------------------------|:-------------------|:-----------|
| **Optimal Combination**     | SL: `N/A`, PT: `100` | N/A        |
| **Final P&L ($)**           | `$124,208.83`         | `$92,543.20`  |
| **CAGR (%)**              | `3.82`%                | `$3.09`%     |
| **Max Drawdown (%)**      | `14.79`%           | `$18.43`%|
| **Calmar Ratio**          | `0.26`                  | `0.17`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)    |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-----------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 93,493.63  |       3.11 |              18.43 |           0.17 |              1 |            100 |
| N/A              | 50                  | 92,064.21  |       3.07 |              18.43 |           0.17 |              2 |            100 |
| N/A              | 100                 | 124,208.83 |       3.82 |              14.79 |           0.26 |              4 |             75 |
| N/A              | 150                 | 93,493.63  |       3.11 |              18.43 |           0.17 |              1 |            100 |
| N/A              | 200                 | 93,493.63  |       3.11 |              18.43 |           0.17 |              1 |            100 |