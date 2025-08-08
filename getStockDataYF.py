import pandas as pd
import pandas_ta as ta
import os
import glob
import numpy as np
import mplfinance as mpf

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
MA_PERIOD = 52
INITIAL_CAPITAL = 100000
COMMISSION_PCT = 0.0005

# <<< Optimization Parameters >>>
TRAILING_STOPS_PCT = [10, 15, 20, 25, 30]
PROFIT_TARGETS_PCT = [None, 50, 100, 150, 200]

def prepare_data(file_path, ma_period):
    """Loads data, ensures index is a timezone-naive datetime, and calculates indicators."""
    try:
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            raise ValueError("Data file must contain Open, High, Low, Close columns.")
        df.ta.sma(length=ma_period, append=True, col_names=(f'SMA_{ma_period}',))
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

def run_backtest(df, trailing_stop_pct, profit_target_pct, initial_capital, commission_pct, sma_col):
    # This function is correct
    in_position = False; entry_price = 0; peak_price_since_entry = 0; num_shares = 0
    cash = initial_capital
    equity_curve = [initial_capital]
    trades_log = []
    for i in range(1, len(df)):
        current_equity = (num_shares * df['Close'].iloc[i-1] if in_position else 0) + cash
        equity_curve.append(current_equity)
        if in_position:
            peak_price_since_entry = max(peak_price_since_entry, df['High'].iloc[i])
            exit_price = -1; exit_reason = ""
            trailing_stop_price = peak_price_since_entry * (1 - trailing_stop_pct / 100)
            if df['Low'].iloc[i] <= trailing_stop_price: 
                exit_price = trailing_stop_price; exit_reason = "Trailing Stop"
            if exit_price == -1 and profit_target_pct is not None:
                profit_target_price = entry_price * (1 + profit_target_pct / 100)
                if df['High'].iloc[i] >= profit_target_price: 
                    exit_price = profit_target_price; exit_reason = "Profit Target"
            if exit_price != -1:
                cash += (num_shares * exit_price) * (1 - commission_pct)
                trades_log[-1].update({'exit_date': df.index[i], 'exit_price': exit_price, 'reason': exit_reason})
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
                    trades_log.append({'entry_date': df.index[i], 'entry_price': entry_price, 'ts_pct': trailing_stop_pct, 'pt_pct': profit_target_pct})
    final_equity = equity_curve[-1]
    if in_position:
        final_equity = (num_shares * df['Close'].iloc[-1]) + cash
        trades_log[-1].update({ 'exit_date': df.index[-1], 'exit_price': df['Close'].iloc[-1], 'reason': 'End of Data'})
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
            "Trailing Stop (%)": trailing_stop_pct, "Profit Target (%)": "None" if profit_target_pct is None else profit_target_pct,
            "P&L ($)": final_pnl, "CAGR (%)": cagr, "Max Drawdown (%)": max_drawdown, 
            "Calmar Ratio": calmar, "Total Trades": len(trades_log), "% Profitable": percent_profitable,
        },
        "trades_log": trades_log
    }

# <<< MODIFIED FUNCTION DEFINITION >>>
def generate_trade_chart(ticker, df, trades_log, sma_col, report_dir, ma_period, ts_pct, pt_pct):
    """Generates and saves a detailed trade chart with a unique, descriptive filename and title."""
    # Create a subdirectory for each ticker to keep plots organized
    plot_dir = os.path.join(report_dir, 'plots', 'individual', ticker)
    os.makedirs(plot_dir, exist_ok=True)
    
    buy_markers = [np.nan] * len(df); sell_markers = [np.nan] * len(df)
    sl_lines = []; pt_lines = []
    
    for trade in trades_log:
        try:
            buy_idx = df.index.get_loc(trade['entry_date']); sell_idx = df.index.get_loc(trade['exit_date'])
            buy_markers[buy_idx] = df['Low'].iloc[buy_idx] * 0.98
            sell_markers[sell_idx] = df['High'].iloc[sell_idx] * 1.02
            if trade.get('pt_pct') is not None:
                pt_price = trade['entry_price'] * (1 + trade['pt_pct'] / 100)
                pt_lines.append([(df.index[buy_idx], pt_price), (df.index[sell_idx], pt_price)])
            if trade.get('reason') == 'Trailing Stop':
                sl_price = trade['exit_price']
                sl_lines.append([(df.index[buy_idx], sl_price), (df.index[sell_idx], sl_price)])
        except KeyError: continue
            
    addplots = [
        mpf.make_addplot(df[sma_col], color='orange'),
        mpf.make_addplot(buy_markers, type='scatter', marker='^', color='g', markersize=100),
        mpf.make_addplot(sell_markers, type='scatter', marker='v', color='r', markersize=100)
    ]

    # <<< NEW: Create descriptive strings for title and filename >>>
    pt_str = 'None' if pt_pct is None else str(pt_pct)
    title_str = f"{ticker} Trades (MA:{ma_period}, TS:{ts_pct}%, PT:{pt_str}%)"
    filename_str = f"{ticker}_{ma_period}_TS{ts_pct}_PT{pt_str}.png"
    chart_filename = os.path.join(plot_dir, filename_str)
    
    all_lines = [*sl_lines, *pt_lines]
    all_colors = [*(['r']*len(sl_lines)), *(['g']*len(pt_lines))]
    
    mpf.plot(df, type='candle', style='yahoo',
             title=title_str, # Use new descriptive title
             ylabel='Price ($)', addplot=addplots,
             alines=dict(lines=all_lines, colors=all_colors, linewidths=0.7, linestyle='--'),
             figratio=(16,9), savefig=dict(fname=chart_filename, dpi=100)) # Use new descriptive filename
    print(f"    - Chart saved: {os.path.basename(chart_filename)}")

def generate_individual_report(ticker, results_df, sweet_spot, bh_stats, report_dir, ma_period, num_years, start_date, end_date):
    # This function is correct
    display_df = results_df.copy()
    for col in ['P&L ($)', 'CAGR (%)', 'Max Drawdown (%)', '% Profitable', 'Calmar Ratio']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")
    md_content = f"# Backtest Report (Individual Asset Focus) for {ticker.upper()}\n\n"
    # ... (rest of the content is correct and remains unchanged) ...
    md_content = f"# Backtest Report (Individual Asset Focus) for {ticker.upper()}\n\n"
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Universe:** This asset ONLY.\n"
    md_content += f"- **Starting Capital:** `${INITIAL_CAPITAL:,.2f}`\n"
    md_content += f"- **Position Sizing:** Each trade uses **100%** of available equity (compounding).\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{ma_period}-period SMA**.\n"
    md_content += f"- **Analysis Period:** {start_date} to {end_date} ({num_years:.1f} years)\n\n"
    md_content += "## Performance Summary\n"
    md_content += "_This table provides an 'apples-to-apples' comparison of the strategy against a Buy & Hold benchmark. Use the **Calmar Ratio** to determine the best risk-adjusted performance._\n\n"
    md_content += "| Metric                  | Strategy (Optimal) | Buy & Hold |\n"
    md_content += "|:------------------------|:-------------------|:-----------|\n"
    md_content += f"| **Optimal Combination**     | T-Stop: `{sweet_spot['Trailing Stop (%)']}%`, P-Target: `{sweet_spot['Profit Target (%)']}` | N/A        |\n"
    md_content += f"| **Final P&L ($)**           | `${sweet_spot['P&L ($)']:,.2f}`         | `${bh_stats['P&L ($)']:,.2f}`  |\n"
    md_content += f"| **CAGR (%)**              | `{sweet_spot['CAGR (%)']:.2f}`%                | `${bh_stats['CAGR (%)']:.2f}`%     |\n"
    md_content += f"| **Max Drawdown (%)**      | `{sweet_spot['Max Drawdown (%)']:.2f}`%           | `${bh_stats['Max Drawdown (%)']:.2f}`%|\n"
    md_content += f"| **Calmar Ratio**          | `{sweet_spot['Calmar Ratio']:.2f}`                  | `${bh_stats['Calmar Ratio']:.2f}`     |\n\n"
    md_content += f"## Full Optimization Grid\n"
    md_content += display_df.to_markdown(index=False)
    report_path = os.path.join(report_dir, f"{ticker}_{ma_period}.md")
    with open(report_path, 'w') as f: f.write(md_content)
    print(f"  - Report saved: {os.path.basename(report_path)}")


def main():
    """Main function for deep-dive analysis, plotting every combination."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files: print("Error: No CSV files found."); return

    print(f"Starting Deep Dive Individual Asset Analysis...\n")
    
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
        
        for ts_pct in TRAILING_STOPS_PCT:
            for pt_pct in PROFIT_TARGETS_PCT:
                print(f"  - Testing TS: {ts_pct}%, PT: {pt_pct or 'None'}")
                result = run_backtest(df, ts_pct, pt_pct, INITIAL_CAPITAL, COMMISSION_PCT, sma_col)
                all_run_results.append(result)
                
                if result['trades_log']:
                    # <<< MODIFIED FUNCTION CALL >>>
                    generate_trade_chart(ticker, df, result['trades_log'], sma_col, REPORTS_DIR, MA_PERIOD, ts_pct, pt_pct)
        
        if not all_run_results: continue
        
        metrics_df = pd.DataFrame([res['metrics'] for res in all_run_results])
        if metrics_df.empty or metrics_df['Calmar Ratio'].isnull().all() or (metrics_df['Calmar Ratio'] <= 0).all():
            print("  No profitable results to create a summary report.")
            continue

        sweet_spot_metrics = max(all_run_results, key=lambda x: x['metrics']['Calmar Ratio'])['metrics']
        generate_individual_report(ticker, metrics_df, sweet_spot_metrics, buy_and_hold_stats, REPORTS_DIR, MA_PERIOD, num_years, start_date_str, end_date_str)

    print("\n--- All individual backtests and plotting complete! ---")

if __name__ == "__main__":
    main()