# Backtest Report (Individual Asset Focus) for SPY

## Backtest Configuration
- **Universe:** This asset ONLY.
- **Starting Capital:** `$100,000.00`
- **Position Sizing:** Each trade uses **100%** of available equity (compounding).
- **Strategy:** Buy on Close crossing above the **52-period SMA**.
- **Stop Loss Mode:** `PREVIOUS_YEAR_LOW`
- **Analysis Period:** 1996-01-02 to 2025-08-06 (29.6 years)

## Performance Summary
_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._

| Metric                  | Strategy (Optimal) | Buy & Hold |
|:------------------------|:-------------------|:-----------|
| **Optimal Combination**     | SL: `N/A`, PT: `50` | N/A        |
| **Final P&L ($)**           | `$4,846,273.36`         | `$1,624,813.03`  |
| **CAGR (%)**              | `14.11`%                | `$10.11`%     |
| **Max Drawdown (%)**      | `44.43`%           | `$55.19`%|
| **Calmar Ratio**          | `0.32`                  | `0.18`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)      |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-------------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 1,643,920.09 |      10.16 |              55.19 |           0.18 |              1 |         100    |
| N/A              | 50                  | 4,846,273.36 |      14.11 |              44.43 |           0.32 |             20 |          80    |
| N/A              | 100                 | 1,768,896.12 |      10.41 |              55.19 |           0.19 |              5 |         100    |
| N/A              | 150                 | 2,001,278.53 |      10.85 |              56.34 |           0.19 |             15 |          73.33 |
| N/A              | 200                 | 4,486,777.18 |      13.82 |              47.52 |           0.29 |              8 |          75    |