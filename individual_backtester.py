import pandas as pd
import pandas_ta as ta
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
MA_PERIOD = 52
INITIAL_CAPITAL = 100000
COMMISSION_PCT = 0.0005

# --- <<< CHOOSE YOUR STRATEGY HERE >>> ---
STOP_LOSS_MODE = 'PREVIOUS_YEAR_LOW' # Options: 'TRAILING', 'FIXED', 'PREVIOUS_YEAR_LOW', 'NONE'

# --- <<< CHOOSE YOUR PLOTTING MODE HERE >>> ---
PLOT_ONLY_OPTIMAL_STRATEGY = True # Set to False to generate a chart for every single combination

# These lists are used for 'TRAILING' and 'FIXED' modes
STOP_LEVELS_PCT = [10, 15, 20, 25, 30]
PROFIT_TARGETS_PCT = [None, 50, 100, 150, 200]

def prepare_data(file_path, ma_period):
    """Loads data and calculates indicators, including previous year's low."""
    try:
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            raise ValueError("Data file must contain Open, High, Low, Close columns.")
        df.ta.sma(length=ma_period, append=True, col_names=(f'SMA_{ma_period}',))
        df['Year'] = df.index.year
        yearly_low = df.groupby('Year')['Low'].min().shift(1)
        df['PrevYearLow'] = df['Year'].map(yearly_low)
        df.ffill(inplace=True)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"  [Error] Could not process {file_path}. Reason: {e}")
        return None

def calculate_benchmark_stats(df, start_capital):
    # This function is correct
    if df.empty or start_capital <= 0: return {"P&L ($)": 0, "CAGR (%)": 0, "Max Drawdown (%)": 0, "Calmar Ratio": 0}
    start_price = df['Open'].iloc[0]
    if start_price <= 0: return {"P&L ($)": 0, "CAGR (%)": 0, "Max Drawdown (%)": 0, "Calmar Ratio": 0}
    end_price = df['Close'].iloc[-1]
    num_shares = start_capital / start_price
    final_equity = num_shares * end_price
    equity_curve = (start_capital / start_price) * df['Close']
    peak = equity_curve.expanding(min_periods=1).max()
    drawdown = (equity_curve - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    num_years = len(df) / 252 
    cagr = ((final_equity / start_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    return { "P&L ($)": final_equity - start_capital, "CAGR (%)": cagr, "Max Drawdown (%)": max_drawdown, "Calmar Ratio": calmar }

def run_backtest(df, stop_loss_mode, stop_level_pct, profit_target_pct, initial_capital, commission_pct, sma_col):
    # This function is correct
    in_position = False; entry_price = 0; peak_price_since_entry = 0; num_shares = 0
    static_stop_price = 0
    cash = initial_capital
    equity_curve = [initial_capital]
    trades_log = []
    trailing_stop_series = [np.nan] * len(df)
    for i in range(1, len(df)):
        current_equity = (num_shares * df['Close'].iloc[i-1] if in_position else 0) + cash
        equity_curve.append(current_equity)
        if in_position:
            exit_price = -1; exit_reason = ""
            if stop_loss_mode == 'TRAILING':
                peak_price_since_entry = max(peak_price_since_entry, df['High'].iloc[i])
                stop_price = peak_price_since_entry * (1 - stop_level_pct / 100)
                trailing_stop_series[i] = stop_price
                if df['Low'].iloc[i] <= stop_price: 
                    exit_price = stop_price; exit_reason = "Trailing Stop"
            elif stop_loss_mode == 'FIXED' or stop_loss_mode == 'PREVIOUS_YEAR_LOW':
                if df['Low'].iloc[i] <= static_stop_price:
                    exit_price = static_stop_price; exit_reason = f"{stop_loss_mode} Stop"
            if exit_price == -1 and profit_target_pct is not None:
                profit_target_price = entry_price * (1 + profit_target_pct / 100)
                if df['High'].iloc[i] >= profit_target_price: 
                    exit_price = profit_target_price; exit_reason = "Profit Target"
            if exit_price != -1:
                cash += (num_shares * exit_price) * (1 - commission_pct)
                trades_log[-1].update({'exit_date': df.index[i], 'exit_price': exit_price, 'reason': exit_reason, 'static_stop': static_stop_price})
                in_position = False; num_shares = 0
        if not in_position and i > 1:
            prev_close, prev_sma = df['Close'].iloc[i-1], df[sma_col].iloc[i-1]
            prev_prev_close, prev_prev_sma = df['Close'].iloc[i-2], df[sma_col].iloc[i-2]
            if prev_prev_close <= prev_prev_sma and prev_close > prev_sma:
                entry_price_candidate = df['Open'].iloc[i]
                if entry_price_candidate > 0:
                    entry_price = entry_price_candidate
                    peak_price_since_entry = entry_price
                    num_shares = (cash * (1-commission_pct)) / entry_price
                    cash = 0
                    in_position = True
                    if stop_loss_mode == 'FIXED': static_stop_price = entry_price * (1 - stop_level_pct / 100)
                    elif stop_loss_mode == 'PREVIOUS_YEAR_LOW': static_stop_price = df['PrevYearLow'].iloc[i]
                    trades_log.append({'entry_date': df.index[i], 'entry_price': entry_price, 'ts_pct': stop_level_pct, 'pt_pct': profit_target_pct})
    if in_position:
        final_equity = (num_shares * df['Close'].iloc[-1]) + cash
        trades_log[-1].update({ 'exit_date': df.index[-1], 'exit_price': df['Close'].iloc[-1], 'reason': 'End of Data', 'static_stop': static_stop_price})
    else: final_equity = equity_curve[-1]
    final_pnl = final_equity - initial_capital
    num_years = len(df) / 252
    cagr = ((final_equity / initial_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    eq_series = pd.Series(equity_curve)
    peak = eq_series.expanding(min_periods=1).max()
    drawdown = (eq_series - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    wins = sum(1 for t in trades_log if t.get('exit_price', 0) > t.get('entry_price', 0))
    percent_profitable = (wins / len(trades_log) * 100) if trades_log else 0
    return {
        "metrics": {
            "Stop Level (%)": stop_level_pct if stop_level_pct is not None else "N/A", 
            "Profit Target (%)": "None" if profit_target_pct is None else profit_target_pct,
            "P&L ($)": final_pnl, "CAGR (%)": cagr, "Max Drawdown (%)": max_drawdown, 
            "Calmar Ratio": calmar, "Total Trades": len(trades_log), "% Profitable": percent_profitable,
        }, "trades_log": trades_log, "trailing_stop_series": trailing_stop_series }

def generate_trade_chart(ticker, df, trades_log, sma_col, report_dir, ma_period, stop_loss_mode, stop_level_pct, pt_pct, trailing_stop_series):
    # This function is correct
    plot_dir = os.path.join(report_dir, 'plots', 'individual', ticker)
    os.makedirs(plot_dir, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(df.index, df['Close'], label='Close Price', color='black', linewidth=1)
    ax.plot(df.index, df[sma_col], label=f'SMA({ma_period})', color='orange', linestyle='--', linewidth=1)
    has_pt_line, has_sl_line = False, False
    for trade in trades_log:
        try:
            ax.plot(trade['entry_date'], trade['entry_price'], '^', color='g', markersize=10)
            ax.plot(trade['exit_date'], trade['exit_price'], 'v', color='r', markersize=10)
            if trade.get('pt_pct') is not None:
                pt_price = trade['entry_price'] * (1 + trade['pt_pct'] / 100)
                ax.hlines(y=pt_price, xmin=trade['entry_date'], xmax=trade['exit_date'], color='g', linestyle='--', linewidth=1.5)
                has_pt_line = True
            if stop_loss_mode == 'FIXED' or stop_loss_mode == 'PREVIOUS_YEAR_LOW':
                sl_price = trade['static_stop']
                ax.hlines(y=sl_price, xmin=trade['entry_date'], xmax=trade['exit_date'], color='r', linestyle='--', linewidth=1.5)
                has_sl_line = True
        except Exception as e: print(f"    - Warning: Could not plot trade due to error: {e}")
    if stop_loss_mode == 'TRAILING':
        ax.plot(df.index, trailing_stop_series, color='r', linestyle='--', linewidth=1.5)
        has_sl_line = True
    sl_str = f"{stop_level_pct}%" if stop_level_pct is not None else "Struct"
    pt_str = 'None' if pt_pct is None else str(pt_pct)
    title = f"{ticker} Trades (MA:{ma_period}, Mode:{stop_loss_mode}, SL:{sl_str}, PT:{pt_str})"
    sl_filename_str = f"{stop_level_pct}" if stop_level_pct is not None else "Struct"
    filename = f"{ticker}_{ma_period}_{stop_loss_mode}_SL{sl_filename_str}_PT{pt_str}.png"
    chart_filename = os.path.join(plot_dir, filename)
    legend_elements = [
        Line2D([0], [0], color='black', lw=1, label='Close Price'),
        Line2D([0], [0], color='orange', linestyle='--', lw=1, label=f'SMA({ma_period})'),
        Line2D([0], [0], marker='^', color='g', label='Buy', markersize=10, ls=''),
        Line2D([0], [0], marker='v', color='r', label='Sell', markersize=10, ls='')]
    if has_pt_line: legend_elements.append(Line2D([0], [0], color='g', linestyle='--', lw=1.5, label='Profit Target'))
    if has_sl_line: legend_elements.append(Line2D([0], [0], color='r', linestyle='--', lw=1.5, label='Stop Loss'))
    ax.set_title(title, fontsize=16)
    ax.legend(handles=legend_elements)
    ax.grid(True); fig.tight_layout()
    plt.savefig(chart_filename, dpi=100); plt.close(fig)
    print(f"  - Chart saved: {os.path.basename(chart_filename)}")

def generate_individual_report(ticker, results_df, sweet_spot, bh_stats, report_dir, ma_period, num_years, start_date, end_date):
    """Generates a detailed individual report with the new directory structure."""
    # <<< THE FIX: Create a ticker-specific subdirectory for the report >>>
    report_subdir = os.path.join(report_dir, 'individual', ticker)
    os.makedirs(report_subdir, exist_ok=True)
    
    display_df = results_df.copy()
    for col in ['P&L ($)', 'CAGR (%)', 'Max Drawdown (%)', '% Profitable', 'Calmar Ratio']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")
    
    md_content = f"# Backtest Report (Individual Asset Focus) for {ticker.upper()}\n\n"
    # ... (rest of report content is correct and remains unchanged) ...
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Universe:** This asset ONLY.\n"
    md_content += f"- **Starting Capital:** `${INITIAL_CAPITAL:,.2f}`\n"
    md_content += f"- **Position Sizing:** Each trade uses **100%** of available equity (compounding).\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{ma_period}-period SMA**.\n"
    md_content += f"- **Stop Loss Mode:** `{STOP_LOSS_MODE}`\n"
    md_content += f"- **Analysis Period:** {start_date} to {end_date} ({num_years:.1f} years)\n\n"
    md_content += "## Performance Summary\n"
    md_content += "_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._\n\n"
    md_content += "| Metric                  | Strategy (Optimal) | Buy & Hold |\n"
    md_content += "|:------------------------|:-------------------|:-----------|\n"
    md_content += f"| **Optimal Combination**     | SL: `{sweet_spot['Stop Level (%)']}`, PT: `{sweet_spot['Profit Target (%)']}` | N/A        |\n"
    md_content += f"| **Final P&L ($)**           | `${sweet_spot['P&L ($)']:,.2f}`         | `${bh_stats['P&L ($)']:,.2f}`  |\n"
    md_content += f"| **CAGR (%)**              | `{sweet_spot['CAGR (%)']:.2f}`%                | `${bh_stats['CAGR (%)']:.2f}`%     |\n"
    md_content += f"| **Max Drawdown (%)**      | `{sweet_spot['Max Drawdown (%)']:.2f}`%           | `${bh_stats['Max Drawdown (%)']:.2f}`%|\n"
    md_content += f"| **Calmar Ratio**          | `{sweet_spot['Calmar Ratio']:.2f}`                  | `{bh_stats['Calmar Ratio']:.2f}`     |\n\n"
    md_content += f"## Full Optimization Grid\n"
    md_content += display_df.to_markdown(index=False)
    
    # <<< THE FIX: Save the report in the new subdirectory >>>
    report_filename = f"{ticker}_{ma_period}_{STOP_LOSS_MODE}.md"
    report_path = os.path.join(report_subdir, report_filename)
    
    with open(report_path, 'w') as f: f.write(md_content)
    print(f"  - Report saved: {os.path.basename(report_path)}")

def main():
    """Main function for multi-mode deep-dive analysis."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files: print("Error: No CSV files found."); return

    print(f"Starting Individual Asset Analysis (Mode: {STOP_LOSS_MODE}, Plotting: {'Optimal Only' if PLOT_ONLY_OPTIMAL_STRATEGY else 'All Combinations'})...\n")
    
    if STOP_LOSS_MODE in ['TRAILING', 'FIXED']:
        stop_levels_to_test = STOP_LEVELS_PCT
    else: stop_levels_to_test = [None] 

    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        print(f"--- Processing {ticker.upper()} ---")
        df = prepare_data(file_path, MA_PERIOD)
        if df is None or df.empty:
            print("  DataFrame is empty after preparation. Skipping.")
            continue
        
        start_date_str = df.index.min().strftime('%Y-%m-%d'); end_date_str = df.index.max().strftime('%Y-%m-%d')
        num_years = len(df) / 252.0
        buy_and_hold_stats = calculate_benchmark_stats(df, INITIAL_CAPITAL)
        sma_col = f'SMA_{MA_PERIOD}'
        all_run_results = []
        
        for sl_pct in stop_levels_to_test:
            for pt_pct in PROFIT_TARGETS_PCT:
                if not PLOT_ONLY_OPTIMAL_STRATEGY:
                    print(f"  - Testing SL: {sl_pct or STOP_LOSS_MODE}, PT: {pt_pct or 'None'}")
                result = run_backtest(df, STOP_LOSS_MODE, sl_pct, pt_pct, INITIAL_CAPITAL, COMMISSION_PCT, sma_col)
                all_run_results.append(result)
                if not PLOT_ONLY_OPTIMAL_STRATEGY and result['trades_log']:
                    generate_trade_chart(ticker, df, result['trades_log'], sma_col, REPORTS_DIR, MA_PERIOD, STOP_LOSS_MODE, sl_pct, pt_pct, result['trailing_stop_series'])
        
        if not all_run_results: continue
        metrics_df = pd.DataFrame([res['metrics'] for res in all_run_results])
        if metrics_df.empty or metrics_df['Calmar Ratio'].isnull().all() or (metrics_df['Calmar Ratio'] <= 0).all():
            print("  No profitable results to create a summary report.")
            continue

        best_run = max(all_run_results, key=lambda x: x['metrics']['Calmar Ratio'])
        sweet_spot_metrics = best_run['metrics']
        
        generate_individual_report(ticker, metrics_df, sweet_spot_metrics, buy_and_hold_stats, REPORTS_DIR, MA_PERIOD, num_years, start_date_str, end_date_str)
        
        if PLOT_ONLY_OPTIMAL_STRATEGY and best_run['trades_log']:
            print("  - Generating chart for optimal strategy...")
            best_sl = sweet_spot_metrics['Stop Level (%)']
            if best_sl == "N/A": best_sl = None
            best_pt_str = sweet_spot_metrics['Profit Target (%)']
            best_pt = None if best_pt_str == "None" else int(best_pt_str)
            generate_trade_chart(ticker, df, best_run['trades_log'], sma_col, REPORTS_DIR, MA_PERIOD, STOP_LOSS_MODE, best_sl, best_pt, best_run['trailing_stop_series'])

    print("\n--- All individual backtests and plotting complete! ---")

if __name__ == "__main__":
    main()