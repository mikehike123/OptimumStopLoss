# Backtest Report (Individual Asset Focus) for GLD

## Backtest Configuration
- **Universe:** This asset ONLY.
- **Starting Capital:** `$100,000.00`
- **Position Sizing:** Each trade uses **100%** of available equity (compounding).
- **Strategy:** Buy on Close crossing above the **52-period SMA**.
- **Stop Loss Mode:** `PREVIOUS_YEAR_LOW`
- **Analysis Period:** 2005-02-02 to 2025-08-06 (20.5 years)

## Performance Summary
_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._

| Metric                  | Strategy (Optimal) | Buy & Hold |
|:------------------------|:-------------------|:-----------|
| **Optimal Combination**     | SL: `N/A`, PT: `50` | N/A        |
| **Final P&L ($)**           | `$677,796.43`         | `$635,433.42`  |
| **CAGR (%)**              | `10.54`%                | `$10.24`%     |
| **Max Drawdown (%)**      | `46.12`%           | `$45.56`%|
| **Calmar Ratio**          | `0.23`                  | `0.22`     |

## Full Optimization Grid
| Stop Level (%)   | Profit Target (%)   | P&L ($)    |   CAGR (%) |   Max Drawdown (%) |   Calmar Ratio |   Total Trades |   % Profitable |
|:-----------------|:--------------------|:-----------|-----------:|-------------------:|---------------:|---------------:|---------------:|
| N/A              | None                | 655,902.65 |      10.38 |              45.56 |           0.23 |              9 |          77.78 |
| N/A              | 50                  | 677,796.43 |      10.54 |              46.12 |           0.23 |             15 |          80    |
| N/A              | 100                 | 622,801.33 |      10.14 |              45.56 |           0.22 |             11 |          81.82 |
| N/A              | 150                 | 572,405.35 |       9.75 |              45.56 |           0.21 |             11 |          81.82 |
| N/A              | 200                 | 633,993.66 |      10.22 |              46.12 |           0.22 |             12 |          75    |