
## Gemini Project State File: `gemini.md`

### Project Title: Quantitative SMA Crossover Strategy Analyzer

**Last Updated:** August 8, 2025

**Project Status:** **Phase 2 Complete.** We have successfully developed two stable, robust, and powerful Python analysis tools: `individual_analyzer.py` and `portfolio_backtester.py`. Both scripts have been thoroughly debugged and are producing logical, insightful results. The primary research questions have been answered, and the platform is now ready for "Phase 3" (new idea generation and testing).

### Core Objective

To build a quantitative framework from the ground up to test a trend-following strategy (SMA Crossover) and determine if active risk management (various stop-loss types, profit targets) can provide a measurable edge ("alpha") over passive Buy & Hold benchmarks in both single-asset and multi-asset portfolio contexts.

### Key Accomplishments & Discoveries

1.  **Two-Tiered Analysis Framework:** We successfully built two distinct but complementary tools:
    *   **`individual_analyzer.py`:** A "deep dive" tool for analyzing a strategy on a single asset in an "all-in," compounding universe. It is invaluable for understanding the pure, undiluted behavior of the strategy on different asset types.
    *   **`portfolio_backtester.py`:** A realistic portfolio simulator that manages a single, shared pool of capital across multiple assets. It incorporates professional-level concepts like dynamic equal-weighting, cash management with interest, and robust benchmarking.

2.  **Strategy Validation:** We proved that for our test universe and timeframe, simple active management rules added significant value. Strategies using **`FIXED`** and **`PREVIOUS_YEAR_LOW`** stops decisively beat the passive benchmarks, achieving both higher returns (CAGR) and lower risk (Max Drawdown). The final **Calmar Ratios** confirmed a superior risk-adjusted performance.

3.  **Visualization is Key:** We developed powerful plotting capabilities for both tools.
    *   **Individual Analyzer:** Generates detailed trade charts (`matplotlib`) showing the price, SMA, buy/sell signals, and the true, dynamic behavior of different stop-loss types (e.g., stair-stepping trailing stops).
    *   **Portfolio Backtester:** Generates a stacked equity chart showing the allocation between `Invested Capital` and `Cash` over time, visually demonstrating the strategy's defensive nature during market downturns.

4.  **Robustness Achieved:** Through an extensive, collaborative debugging process, we have made the tools resilient to common data issues (timezones, short histories, zero prices) and logical fallacies (cash drag, survivorship bias awareness, fair benchmarking).

### Current State of the Code

*   **`individual_analyzer.py`:** This script is **complete and stable**. It is multi-modal, allowing the user to select between `TRAILING`, `FIXED`, `PREVIOUS_YEAR_LOW`, and `NONE` for the stop-loss logic. It also has a configurable flag (`PLOT_ONLY_OPTIMAL_STRATEGY`) to switch between a quick summary mode and a deep-dive plotting mode. The reporting is clean, comprehensive, and includes a fair "apples-to-apples" benchmark comparison.

*   **`portfolio_backtester.py`:** This script is also **complete and stable**. It is multi-modal and mirrors the logic of the individual analyzer but within a realistic portfolio context. It generates a single, definitive summary report comparing the optimal active strategy against two robust benchmarks.

### Future Research Paths ("Phase 3")

The platform is now perfectly poised to investigate the new hypotheses we've developed:

1.  **Structure-Based Exits:** The success of the `PREVIOUS_YEAR_LOW` stop suggests that other market structure-based stops could be very powerful. The next logical step is to implement a **Chandelier Exit** (stop at `highest_high_since_entry - N * ATR`). This would make the stop adaptive to volatility.

2.  **Contrarian Entry Signals:** Explore the "buy the dip" idea. We could design and test a new entry signal based on buying when the price falls a certain distance *below* its moving average, looking for mean-reversion opportunities.

3.  **Volatility-Based Position Sizing:** A major potential enhancement to the portfolio backtester would be to move beyond equal-weighting. We could implement a system where more volatile assets are given a smaller capital allocation and less volatile assets are given a larger one, aiming to equalize the risk contribution of each position.

This has been a fantastic and incredibly productive project. I'm ready to pick up with Phase 3 whenever you are.