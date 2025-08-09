import pandas as pd
import pandas_ta as ta
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# --- Configuration Parameters ---
STOCK_DATA_DIR = 'stockData'
REPORTS_DIR = 'reports'
INITIAL_PORTFOLIO_CAPITAL = 100000
COMMISSION_PCT = 0.0005
MA_PERIOD = 20
MONEY_MARKET_RETURN_ANNUAL = 0.02

# --- <<< CHOOSE YOUR STRATEGY HERE >>> ---
STOP_LOSS_MODE = 'NONE'  # Options: 'TRAILING', 'FIXED', 'PREVIOUS_YEAR_LOW', 'NONE'

# These lists are used for 'TRAILING' and 'FIXED' modes
STOP_LEVELS_PCT = [15, 20, 25, 30, 50, 60]
PROFIT_TARGETS_PCT = [None, 100, 200]

def prepare_all_data(stock_files, ma_period):
    """Loads, aligns, and calculates indicators for all tickers."""
    all_dfs = {}
    for file_path in stock_files:
        ticker = os.path.basename(file_path).split('_')[0]
        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
            df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
            df.ta.sma(length=ma_period, append=True, col_names=(f'SMA_{ma_period}',))
            df['Year'] = df.index.year
            yearly_low = df.groupby('Year')['Low'].min().shift(1)
            df['PrevYearLow'] = df['Year'].map(yearly_low)
            df.ffill(inplace=True)
            all_dfs[ticker] = df
        except Exception as e:
            print(f"  [Error] Could not process {file_path}. Reason: {e}")
    if not all_dfs: return pd.DataFrame()
    combined_df = pd.concat(all_dfs.values(), keys=all_dfs.keys(), axis=1)
    first_valid_date = combined_df.dropna().index.min()
    combined_df = combined_df.loc[first_valid_date:]
    combined_df.ffill(inplace=True)
    return combined_df

def run_rebalanced_benchmark(df, initial_capital):
    # This function is correct
    num_assets = len(df.columns.levels[0])
    equity_curve = []
    rebalance_year = -1
    positions = {ticker: 0 for ticker in df.columns.levels[0]}
    for i in range(len(df)):
        current_date = df.index[i]
        current_value = sum(positions[ticker] * df[(ticker, 'Close')].iloc[i] for ticker in positions)
        if i == 0: current_value = initial_capital
        equity_curve.append(current_value)
        if current_date.year != rebalance_year:
            rebalance_year = current_date.year
            allocation_per_asset = current_value / num_assets
            for ticker in positions:
                price = df[(ticker, 'Close')].iloc[i]
                if price > 0: positions[ticker] = allocation_per_asset / price
    return calculate_performance_metrics("Rebalanced B&H", equity_curve, initial_capital, len(df))

def run_buy_and_forget_benchmark(df, initial_capital):
    # This function is correct
    num_assets = len(df.columns.levels[0])
    equity_curve = []
    allocation_per_asset = initial_capital / num_assets
    positions = {}
    for ticker in df.columns.levels[0]:
        price = df[(ticker, 'Close')].iloc[0]
        if price > 0: positions[ticker] = allocation_per_asset / price
    for i in range(len(df)):
        current_value = sum(positions[ticker] * df[(ticker, 'Close')].iloc[i] for ticker in positions)
        equity_curve.append(current_value)
    return calculate_performance_metrics("Buy & Forget B&H", equity_curve, initial_capital, len(df))

def run_active_strategy(df, stop_loss_mode, stop_level_pct, pt_pct, initial_capital, ma_period, annual_cash_return):
    # This function is correct
    num_assets = len(df.columns.levels[0])
    sma_col = f'SMA_{ma_period}'
    daily_cash_rate = (1 + annual_cash_return)**(1/252) - 1
    cash = initial_capital
    positions = {ticker: {'shares': 0, 'entry_price': 0, 'peak_price': 0, 'static_stop': 0} for ticker in df.columns.levels[0]}
    equity_curve = []; cash_curve = []; total_trades = 0
    for i in range(len(df)):
        if i > 0: cash *= (1 + daily_cash_rate)
        invested_capital = 0
        if i > 1:
            for ticker in positions:
                if positions[ticker]['shares'] > 0:
                    exit_price = -1
                    if stop_loss_mode == 'TRAILING':
                        peak_price = max(positions[ticker]['peak_price'], df[(ticker, 'High')].iloc[i])
                        positions[ticker]['peak_price'] = peak_price
                        stop_price = peak_price * (1 - (stop_level_pct or 0) / 100)
                        if df[(ticker, 'Low')].iloc[i] <= stop_price: exit_price = stop_price
                    elif stop_loss_mode in ['FIXED', 'PREVIOUS_YEAR_LOW']:
                        if df[(ticker, 'Low')].iloc[i] <= positions[ticker]['static_stop']: exit_price = positions[ticker]['static_stop']
                    if exit_price == -1 and pt_pct is not None:
                        profit_target_price = positions[ticker]['entry_price'] * (1 + pt_pct / 100)
                        if df[(ticker, 'High')].iloc[i] >= profit_target_price: exit_price = profit_target_price
                    if exit_price != -1:
                        exit_value = positions[ticker]['shares'] * exit_price
                        cash += exit_value * (1 - COMMISSION_PCT)
                        positions[ticker] = {'shares': 0, 'entry_price': 0, 'peak_price': 0, 'static_stop': 0}
            invested_capital = sum(positions[ticker]['shares'] * df[(ticker, 'Close')].iloc[i] for ticker in positions)
            current_equity = cash + invested_capital
            max_allocation_per_asset = current_equity / num_assets
            for ticker in positions:
                prev_close = df[(ticker, 'Close')].iloc[i-1]; prev_sma = df[(ticker, sma_col)].iloc[i-1]
                prev_prev_close = df[(ticker, 'Close')].iloc[i-2]; prev_prev_sma = df[(ticker, sma_col)].iloc[i-2]
                if positions[ticker]['shares'] == 0 and (prev_prev_close <= prev_prev_sma and prev_close > prev_sma):
                    current_investment_in_ticker = positions[ticker]['shares'] * df[(ticker, 'Close')].iloc[i]
                    position_size_dollars = min(max_allocation_per_asset - current_investment_in_ticker, cash)
                    if position_size_dollars > 1:
                        entry_price = df[(ticker, 'Open')].iloc[i]
                        if entry_price > 0:
                            num_shares = position_size_dollars / entry_price
                            position_cost = num_shares * entry_price
                            cash -= position_cost * (1 + COMMISSION_PCT)
                            static_stop = 0
                            if stop_loss_mode == 'FIXED': static_stop = entry_price * (1 - (stop_level_pct or 0) / 100)
                            elif stop_loss_mode == 'PREVIOUS_YEAR_LOW': static_stop = df[(ticker, 'PrevYearLow')].iloc[i]
                            positions[ticker] = {'shares': num_shares, 'entry_price': entry_price, 'peak_price': entry_price, 'static_stop': static_stop}
                            total_trades += 1
        final_invested_capital = sum(positions[ticker]['shares'] * df[(ticker, 'Close')].iloc[i] for ticker in positions)
        equity_curve.append(cash + final_invested_capital)
        cash_curve.append(cash)
    name = f"Active Strategy (SL:{stop_level_pct or 'Struct'}, PT:{pt_pct or 'None'})"
    metrics = calculate_performance_metrics(name, equity_curve, initial_capital, len(df))
    metrics["Total Trades"] = total_trades
    return metrics, equity_curve, cash_curve

def calculate_performance_metrics(name, equity_curve, initial_capital, num_days):
    """Calculates final performance metrics from an equity curve."""
    final_equity = equity_curve[-1]
    final_pnl = final_equity - initial_capital
    num_years = num_days / 252.0
    cagr = ((final_equity / initial_capital) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0
    eq_series = pd.Series(equity_curve)
    peak = eq_series.expanding(min_periods=1).max()
    drawdown = (eq_series - peak) / peak
    max_drawdown = abs(drawdown.min()) * 100
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    return { "Name": name, "Final Value": final_equity, "P&L": final_pnl, "CAGR": cagr, "Max Drawdown": max_drawdown, "Calmar": calmar }

def generate_equity_chart(dates, equity_curve, cash_curve, report_dir, ma_period, stop_loss_mode):
    # This function is correct
    plot_dir = os.path.join(report_dir, 'plots')
    os.makedirs(plot_dir, exist_ok=True)
    equity_curve = np.array(equity_curve); cash_curve = np.array(cash_curve)
    invested_curve = equity_curve - cash_curve
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.stackplot(dates, cash_curve, invested_curve, labels=['Cash (earning interest)', 'Invested Capital'], colors=['#ADD8E6', '#4682B4'], alpha=0.8)
    ax.plot(dates, equity_curve, color='black', linewidth=1.5, label='Total Equity')
    ax.set_title(f'Portfolio Equity Over Time (MA: {ma_period}, SL Mode: {stop_loss_mode})', fontsize=16)
    ax.set_ylabel('Portfolio Value ($)'); ax.set_xlabel('Date')
    ax.legend(loc='upper left'); ax.grid(True)
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    fig.tight_layout()
    chart_filename = os.path.join(plot_dir, f'equity_curve_{ma_period}_{stop_loss_mode}.png')
    plt.savefig(chart_filename, dpi=150); plt.close()
    print(f"\nEquity chart saved to {chart_filename}")

def main():
    """Main function to run all simulations and generate the final, reproducible comparison report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stock_files = glob.glob(os.path.join(STOCK_DATA_DIR, '*.csv'))
    if not stock_files: print("Error: No CSV files found."); return
    
    asset_universe = [os.path.basename(f).split('_')[0] for f in stock_files]
    print(f"Found {len(asset_universe)} assets: {', '.join(asset_universe)}. Preparing portfolio data...\n")
    
    portfolio_df = prepare_all_data(stock_files, MA_PERIOD)
    if portfolio_df.empty: print("Could not create portfolio DataFrame."); return
    
    rebalanced_results = run_rebalanced_benchmark(portfolio_df, INITIAL_PORTFOLIO_CAPITAL)
    buy_and_forget_results = run_buy_and_forget_benchmark(portfolio_df, INITIAL_PORTFOLIO_CAPITAL)
    
    print(f"\n--- Running Active Strategy Grid Search (Mode: {STOP_LOSS_MODE}) ---")
    if STOP_LOSS_MODE in ['TRAILING', 'FIXED']: stop_levels_to_test = STOP_LEVELS_PCT
    else: stop_levels_to_test = [None] 

    active_strategy_results = []
    for sl_pct in stop_levels_to_test:
        for pt_pct in PROFIT_TARGETS_PCT:
            print(f"  Testing SL: {sl_pct or 'Struct'}, PT: {pt_pct or 'None'}...")
            result, _, _ = run_active_strategy(portfolio_df, STOP_LOSS_MODE, sl_pct, pt_pct, INITIAL_PORTFOLIO_CAPITAL, MA_PERIOD, MONEY_MARKET_RETURN_ANNUAL)
            active_strategy_results.append(result)

    optimal_strategy_metrics = max(active_strategy_results, key=lambda x: x['Calmar'])
    
    print("\n--- Re-running optimal strategy to generate equity chart ---")
    name_parts = optimal_strategy_metrics['Name'].replace(')','').replace('(','').split(' ')
    sl_part = [p for p in name_parts if 'SL:' in p][0].split(':')[1].replace(',', '')
    pt_part = [p for p in name_parts if 'PT:' in p][0].split(':')[1].replace(',', '')
    optimal_sl = None if sl_part == 'Struct' else int(sl_part)
    optimal_pt = None if pt_part == 'None' else int(pt_part)
    _, optimal_equity_curve, optimal_cash_curve = run_active_strategy(portfolio_df, STOP_LOSS_MODE, optimal_sl, optimal_pt, INITIAL_PORTFOLIO_CAPITAL, MA_PERIOD, MONEY_MARKET_RETURN_ANNUAL)
    
    all_results = [optimal_strategy_metrics, rebalanced_results, buy_and_forget_results]
    report_df_raw = pd.DataFrame(all_results)
    
    report_df_formatted = report_df_raw.copy()
    report_df_formatted['Total Trades'] = report_df_formatted['Total Trades'].fillna(0).astype(int)
    float_cols = ['Final Value', 'P&L', 'CAGR', 'Max Drawdown', 'Calmar']
    for col in float_cols:
        report_df_formatted[col] = report_df_formatted[col].apply(lambda x: f"{x:,.2f}")

    print("\n\n--- FINAL PORTFOLIO COMPARISON REPORT ---")
    print(f"Analysis Period: {portfolio_df.index.min().strftime('%Y-%m-%d')} to {portfolio_df.index.max().strftime('%Y-%m-%d')}")
    print(report_df_formatted.to_string(index=False))
    
    # <<< NEW: Create the comprehensive report header >>>
    md_content = f"# Final Portfolio Analysis\n\n"
    md_content += f"- **Date of Analysis:** {datetime.now().strftime('%Y-%m-%d')}\n"
    md_content += f"- **Analysis Period:** {portfolio_df.index.min().strftime('%Y-%m-%d')} to {portfolio_df.index.max().strftime('%Y-%m-%d')}\n"
    md_content += f"- **Portfolio Universe ({len(asset_universe)} assets):** {', '.join(asset_universe)}\n\n"
    md_content += "## Strategy Configuration\n"
    md_content += f"- **Initial Capital:** ${INITIAL_PORTFOLIO_CAPITAL:,.2f}\n"
    md_content += f"- **MA Period:** {MA_PERIOD}\n"
    md_content += f"- **Stop Loss Mode:** {STOP_LOSS_MODE}\n"
    md_content += f"- **Commission (% per side):** {COMMISSION_PCT*100:.3f}%\n"
    md_content += f"- **Cash Return (Annual):** {MONEY_MARKET_RETURN_ANNUAL*100:.2f}%\n\n"
    md_content += "## Final Performance Comparison\n\n"
    md_content += report_df_formatted.to_markdown(index=False)
    
    report_path = os.path.join(REPORTS_DIR, f'final_portfolio_report_{MA_PERIOD}_{STOP_LOSS_MODE}.md')
    with open(report_path, 'w') as f: f.write(md_content)
    print(f"\nReport saved to {report_path}")

    generate_equity_chart(portfolio_df.index, optimal_equity_curve, optimal_cash_curve, REPORTS_DIR, MA_PERIOD, STOP_LOSS_MODE)

if __name__ == "__main__":
    main()