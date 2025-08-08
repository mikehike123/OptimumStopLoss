Here is a comprehensive `README.md` file. It is structured to guide a new user logically from the concept to the final interpretation of the results.

---

# Quantitative Trend-Following Strategy Analyzer

This project provides a complete, end-to-end framework for backtesting and analyzing a classic trend-following strategy based on a Simple Moving Average (SMA) crossover. It contains two primary analysis tools: a deep-dive single-asset analyzer and a sophisticated multi-asset portfolio simulator.

The core objective of this research platform is to empirically evaluate whether various risk management techniques, specifically different types of stop-losses and profit targets, can be used to mitigate risk and improve returns compared to simple Buy & Hold benchmarks.

## Project Structure

```
/
|-- stockData/
|   |-- SPY_1d.csv
|   |-- QQQ_1d.csv
|   `-- ... (other data files)
|
|-- reports/
|   |-- plots/
|   |   |-- individual/
|   |   |   |-- SPY/
|   |   |   |   |-- SPY_52_TRAILING_SL15_PT100.png
|   |   |   |   `-- ... (other plot files)
|   |   |
|   |   `-- portfolio/
|   |       `-- equity_curve_52_TRAILING.png
|   |
|   |-- individual/
|   |   |-- SPY/
|   |   |   |-- SPY_52_TRAILING.md
|   |   |   `-- ... (other report files)
|   |
|   `-- final_portfolio_report_52_TRAILING.md
|
|-- getStockDataYF.py
|-- individual_analyzer.py
|-- portfolio_backtester.py
`-- README.md
```

## The Process: A Step-by-Step Guide

### Step 1: Setting Up the Environment

This project uses a dedicated Conda environment to manage its dependencies, ensuring a clean and reproducible setup.

1.  Open the Anaconda Prompt (or your terminal).
2.  Create the environment:
    ```bash
    conda create --name stoploss python=3.11
    ```
3.  Activate the environment:
    ```bash
    conda activate stoploss
    ```
4.  Install all necessary packages from the trusted `conda-forge` channel:
    ```bash
    conda install -c conda-forge pandas pandas-ta matplotlib
    ```

### Step 2: Downloading Historical Data

The `getStockDataYF.py` script uses the `yfinance` library to download historical daily price data from Yahoo Finance.

1.  **Configure:** Open `getStockDataYF.py` and modify the `tickers` list to include the assets you wish to analyze.
2.  **Run:** Execute the script from your terminal:
    ```bash
    python getStockDataYF.py
    ```
3.  **Output:** This will populate the `stockData/` directory with the required CSV files.

### Step 3: Deep-Dive Single-Asset Analysis

The `individual_analyzer.py` script is a powerful tool for understanding how the strategy behaves on a **single asset in isolation**. It simulates a universe where 100% of your capital is dedicated to trading only that one asset.

**How it Works:**
*   It performs a "grid search," testing every combination of `TRAILING_STOPS_PCT` and `PROFIT_TARGETS_PCT`.
*   For each combination, it generates a detailed trade chart showing every buy, sell, stop-loss, and profit-target.
*   It then generates a summary report for the asset, highlighting the optimal parameter set (based on the highest risk-adjusted return) and comparing it to a Buy & Hold benchmark.

**Configuration:**
Open `individual_analyzer.py` and set the following parameters at the top of the file:
*   `MA_PERIOD`: The lookback period for the Simple Moving Average (e.g., 52 for a weekly equivalent on a daily chart).
*   `STOP_LOSS_MODE`: Choose the risk management philosophy to test.
    *   `'TRAILING'`: A stop-loss that ratchets up as a trade moves in your favor.
    *   `'FIXED'`: A simple stop-loss based on the entry price.
    *   `'PREVIOUS_YEAR_LOW'`: A structural stop based on the market's own history.
    *   `'NONE'`: No stop-loss is used.
*   `PLOT_ONLY_OPTIMAL_STRATEGY`: Set to `True` for a fast analysis that only plots the best result. Set to `False` for a "deep dive" that plots every single combination (generates many files).

**Run:**
```bash
python individual_analyzer.py
```

### Step 4: Realistic Portfolio-Level Simulation

The `portfolio_backtester.py` script is the definitive analysis tool. It simulates how the strategy performs in a more realistic environment where a **single pool of capital is shared across a diversified portfolio of assets.**

**How it Works & Manages Cash:**
*   **Shared Capital:** The simulation starts with a single `$100,000` account.
*   **Dynamic Allocation:** It enforces a "Dynamic Equal-Weighting" rule. The maximum capital that can be allocated to any single asset is `current_portfolio_equity / number_of_assets`. This prevents over-concentration and allows position sizes to grow as the portfolio compounds.
*   **Cash Management:** It tracks cash on a daily basis. Idle cash earns a simulated money market return. A "No Cash, No Trade" rule is enforced, meaning a signal is ignored if there isn't enough cash to take the position.
*   **Optimization:** It runs a full grid search to find the single "house rule" (the optimal combination of stop-loss and profit-target) that produces the best risk-adjusted return for the entire portfolio.
*   **Benchmarking:** It compares the optimal active strategy against two powerful benchmarks: an annually rebalanced equal-weighted portfolio and a "buy-and-forget" portfolio.

**Configuration:**
Open `portfolio_backtester.py` and set the core strategy parameters at the top of the file, just like in the individual analyzer.

**Run:**
```bash
python portfolio_backtester.py
```

## Interpreting the Results: What Have We Learned?

The primary objective was to evaluate if active risk management could improve on simple benchmarks. The results from our analysis, particularly on a diversified basket of ETFs, were conclusive.

1.  **Active Management Adds Significant Value:** Both the `FIXED` stop-loss and the `PREVIOUS_YEAR_LOW` structural stop produced portfolio-level results that were superior to the benchmarks. They generated a **higher Compound Annual Growth Rate (CAGR)** while simultaneously subjecting the portfolio to a **lower Max Drawdown**.

2.  **Superior Risk-Adjusted Returns:** The key metric is the **Calmar Ratio (CAGR / Max Drawdown)**. Our optimal active strategies consistently produced a higher Calmar Ratio than either of the benchmarks. This provides a data-driven answer to our core question: **Yes, this strategy's risk management rules successfully mitigated risk and improved returns** compared to passive alternatives over the tested period.

3.  **The Power of Visualization:** The generated charts are essential. The portfolio equity chart visualizes how the strategy intelligently moves to cash during market downturns (like 2008), mitigating losses. The individual trade charts reveal the specific behavior of the exit rules, showing (for example) how a tight trailing stop can be "whipsawed" in choppy markets.

This framework provides a robust and reliable platform for further quantitative research.