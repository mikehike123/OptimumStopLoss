import pandas as pd
import pandas_ta as ta
import os
import glob

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
MA_PERIOD = 52
ATR_PERIOD = 14
STOP_LOSSES_PCT = [1, 3, 5, 7, 10, 15, 20, 25, 30]
INITIAL_CAPITAL = 100000
COMMISSION_PCT = 0.0005
POSITION_SIZE_PCT = 0.10

def prepare_data(file_path, ma_period, atr_period):
    """Loads data, ensures index is a timezone-naive datetime, and calculates indicators."""
    try:
        df = pd.read_csv(file_path, index_col='Date')
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        df.ta.sma(length=ma_period, append=True, col_names=(f'SMA_{ma_period}',))
        df.ta.atr(length=atr_period, append=True, col_names=(f'ATR_{atr_period}',))
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"  [Error] Could not process {file_path}. Reason: {e}")
        return None

def run_backtest(df, stop_loss_pct, initial_capital, commission_pct, sma_col):
    """Runs the backtest with realistic position sizing."""
    in_position = False
    equity = initial_capital
    consecutive_losses = 0
    entry_price = 0
    position_size_dollars = initial_capital * POSITION_SIZE_PCT
    trades = []

    for i in range(2, len(df)):
        if in_position:
            stop_price = entry_price * (1 - stop_loss_pct / 100)
            if df['Low'].iloc[i] <= stop_price:
                num_shares = position_size_dollars / entry_price
                pnl_dollars = (stop_price - entry_price) * num_shares
                equity += pnl_dollars - ((stop_price * num_shares) * commission_pct)
                trades.append({"pnl_dollars": pnl_dollars})
                consecutive_losses += 1
                in_position = False

        prev_close, prev_sma = df['Close'].iloc[i-1], df[sma_col].iloc[i-1]
        prev_prev_close, prev_prev_sma = df['Close'].iloc[i-2], df[sma_col].iloc[i-2]
        
        if not in_position and prev_prev_close <= prev_prev_sma and prev_close > prev_sma:
            entry_price_candidate = df['Open'].iloc[i]
            if entry_price_candidate > 0:
                entry_price = entry_price_candidate
                equity -= position_size_dollars * commission_pct
                in_position = True

    if in_position and entry_price > 0:
        num_shares = position_size_dollars / entry_price
        unrealized_pnl = (df['Close'].iloc[-1] - entry_price) * num_shares
        equity += unrealized_pnl

    final_pnl = equity - initial_capital
    total_losses = sum(t['pnl_dollars'] for t in trades)
    max_drawdown = abs(total_losses) / initial_capital if initial_capital > 0 else 0

    return {
        "Stop Loss (%)": stop_loss_pct,
        "Total Trades": len(trades),
        "P&L ($)": final_pnl,
        "Max Equity Drawdown (%)": max_drawdown * 100,
        "Max Stock Loss Streak": consecutive_losses,
    }

def generate_individual_report(ticker, results_df, sweet_spot, report_dir, ma_period):
    """Creates a detailed Markdown report for a single stock/ETF with MA in filename."""
    display_df = results_df.copy()
    for col in ['P&L ($)', 'Max Equity Drawdown (%)']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}")
    
    md_content = f"# Backtest Report for {ticker.upper()}\n\n"
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{ma_period}-period SMA**.\n"
    md_content += f"- **Position Sizing:** Each trade allocates **{POSITION_SIZE_PCT:.0%}** of initial capital.\n\n"
    md_content += f"## Optimal Result (Sweet Spot)\n"
    md_content += f"- **Optimal Stop Loss:** `{sweet_spot['Stop Loss (%)']}%`\n"
    md_content += f"- **P&L at Sweet Spot:** `${sweet_spot['P&L ($)']:,.2f}`\n\n"
    md_content += f"## Full Performance Table\n"
    md_content += display_df.to_markdown(index=False)
    
    report_path = os.path.join(report_dir, f"{ticker}_{ma_period}.md")
    
    with open(report_path, 'w') as f:
        f.write(md_content)
    print(f"  Individual report for {ticker} saved.")

def generate_summary_report(summary_data, group_sweet_spot, start_date, end_date, report_dir):
    """Creates the final summary report with portfolio optimal results."""
    if not summary_data: return

    summary_df = pd.DataFrame(summary_data)
    summary_df.rename(columns={"Stop Loss (%)": "Optimal SL (%)"}, inplace=True)
    
    group_df = pd.DataFrame([group_sweet_spot])
    group_df.rename(columns={"Stop Loss (%)": "Optimal SL (%)"}, inplace=True)
    
    final_df = pd.concat([summary_df, group_df], ignore_index=True)
    cols_order = ["Symbol", "Optimal SL (%)", "P&L ($)", "Max Equity Drawdown (%)", "Total Trades", "Max Stock Loss Streak"]
    final_df = final_df[cols_order]
    
    for col in ['P&L ($)', 'Max Equity Drawdown (%)']:
        if col in final_df.columns:
            final_df[col] = final_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)

    md_content = f"# Strategy Summary & Portfolio Optimization Report\n\n"
    md_content += "## Backtest Configuration\n"
    md_content += f"- **Strategy:** Buy on Close crossing above the **{MA_PERIOD}-period SMA**.\n"
    md_content += f"- **Position Sizing:** Each trade allocates **{POSITION_SIZE_PCT:.0%}** of initial capital.\n"
    md_content += f"- **Analysis Date Range:** {start_date} to {end_date}\n\n"
    md_content += "## Portfolio Optimal Result\n"
    md_content += "The following rule was found by summing the total P&L for every stop-loss across all stocks.\n\n"
    md_content += f"- **Optimal Group Stop-Loss:** **{group_sweet_spot['Stop Loss (%)']}%**\n"
    md_content += f"- **Aggregate Portfolio P&L:** **${group_sweet_spot['P&L ($)']:,.2f}**\n\n"
    md_content += "## Results Table\n"
    md_content += "The table shows the individual sweet spot for each asset, followed by the combined result when applying the single portfolio-optimal rule.\n\n"
    md_content += final_df.to_markdown(index=False)

    report_path = os.path.join(report_dir, f'summary_report_{MA_PERIOD}.md')
    with open(report_path, 'w') as f:
        f.write(md_content)
    print(f"\nMaster summary report saved to: {report_path}")

def main():
    """Main function to orchestrate the backtesting and reporting."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files:
        print(f"Error: No CSV files found in '{STOCK_DATA_DIR}'.")
        return

    print(f"Found {len(stock_files)} stocks. Starting backtests...\n")
    
    individual_sweet_spots = []
    all_results_matrix = []
    min_start_date, max_end_date = pd.Timestamp.max, pd.Timestamp.min

    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        print(f"--- Processing {ticker.upper()} ---")

        df = prepare_data(file_path, MA_PERIOD, ATR_PERIOD)
        if df is None: continue

        min_start_date = min(min_start_date, df.index.min())
        max_end_date = max(max_end_date, df.index.max())
        sma_col = f'SMA_{MA_PERIOD}'
        
        results_this_stock = []
        for sl_pct in STOP_LOSSES_PCT:
            result = run_backtest(df, sl_pct, INITIAL_CAPITAL, COMMISSION_PCT, sma_col)
            results_this_stock.append(result)
            all_results_matrix.append({'ticker': ticker, 'sl_pct': sl_pct, 'pnl': result['P&L ($)']})
        
        if not any(res.get("Total Trades", 0) > 0 for res in results_this_stock):
            print("  No trades executed. Skipping.")
            continue
            
        results_df = pd.DataFrame(results_this_stock)
        sweet_spot = results_df.loc[results_df['P&L ($)'].idxmax()].to_dict()
        sweet_spot['Symbol'] = ticker.upper()
        
        generate_individual_report(ticker, results_df, sweet_spot, REPORTS_DIR, MA_PERIOD)
        
        individual_sweet_spots.append(sweet_spot)
    
    if not all_results_matrix:
        print("\nNo trades were executed across any stocks. Cannot generate report.")
        return

    matrix_df = pd.DataFrame(all_results_matrix)
    group_pnl = matrix_df.groupby('sl_pct')['pnl'].sum()
    portfolio_optimal_sl = group_pnl.idxmax()
    
    total_trades, max_stock_loss_streak_overall = 0, 0
    for file_path in stock_files:
         df = prepare_data(file_path, MA_PERIOD, ATR_PERIOD)
         if df is None: continue
         sma_col = f'SMA_{MA_PERIOD}'
         result = run_backtest(df, portfolio_optimal_sl, INITIAL_CAPITAL, COMMISSION_PCT, sma_col)
         total_trades += result['Total Trades']
         if result['Max Stock Loss Streak'] > max_stock_loss_streak_overall:
             max_stock_loss_streak_overall = result['Max Stock Loss Streak']
             
    group_sweet_spot = {
        'Symbol': '**PORTFOLIO OPTIMAL**',
        'Stop Loss (%)': portfolio_optimal_sl,
        'P&L ($)': group_pnl.max(),
        'Total Trades': total_trades,
        'Max Stock Loss Streak': max_stock_loss_streak_overall,
        'Max Equity Drawdown (%)': 'N/A'
    }
    
    generate_summary_report(
        individual_sweet_spots, 
        group_sweet_spot,
        min_start_date.strftime('%Y-%m-%d'), 
        max_end_date.strftime('%Y-%m-%d'), 
        REPORTS_DIR
    )
    
    print("\n--- All backtests complete! ---")

if __name__ == "__main__":
    main()