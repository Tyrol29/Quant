"""
Week 1 - MACD金叉死叉策略回测（沪深300市值前40只股票）
============================================================
本文件演示：
1. 获取沪深300成分股中市值前40的股票
2. 使用MACD金叉死叉策略进行回测
3. 计算收益率、波动率、夏普比率、阿尔法收益、贝塔收益等指标

策略说明：
- 金叉（DIF上穿DEA）：全仓买入
- 死叉（DIF下穿DEA）：全仓卖出
- 每只股票初始资金：15万元
- 数据时间范围：近两年（约504个交易日）

依赖安装：
    pip install tushare pandas numpy matplotlib

API Token: 877cd5e05fb5edf3115e7a26e16741c4333d07a1216168bde06e781c
"""

import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# ==================== 配置 ====================
TUSHARE_TOKEN = "877cd5e05fb5edf3115e7a26e16741c4333d07a1216168bde06e781c"

# 回测参数
INITIAL_CAPITAL_PER_STOCK = 150000  # 每只股票初始资金 15万元
TOP_N_STOCKS = 20  # 选取前20只股票

# 注意：当前Token只有120积分，只能使用daily接口
# 因此无法获取指数数据，Alpha和Beta指标将无法计算
START_DATE = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')  # 两年前
END_DATE = datetime.now().strftime('%Y%m%d')  # 今天

# API限制参数
API_CALL_DELAY = 1.2  # API调用间隔(秒)，避免触发每分钟50次的限制

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ==================== 1. Tushare 数据获取 ====================
def init_tushare():
    """初始化 Tushare API"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    return pro


def get_hs300_stocks(pro, top_n=TOP_N_STOCKS):
    """
    获取沪深300成分股中市值前N的股票
    
    注意：当前token权限无法使用index_weight和daily_basic接口
    使用预设的沪深300成分股股票池（按市值从大到小排序）
    
    参数:
        pro: Tushare API 对象
        top_n: 选取市值前N的股票，默认40
    
    返回:
        DataFrame: 包含股票代码和名称
    """
    print(f"正在准备沪深300成分股中市值前{top_n}的股票...")
    
    # 预设的沪深300成分股（已按市值从大到小排序，前40只为大盘股）
    STOCK_POOL = [
        ('600519.SH', '贵州茅台'), ('300750.SZ', '宁德时代'), ('601318.SH', '中国平安'),
        ('600036.SH', '招商银行'), ('000858.SZ', '五粮液'), ('601012.SH', '隆基绿能'),
        ('000333.SZ', '美的集团'), ('002594.SZ', '比亚迪'), ('600900.SH', '长江电力'),
        ('600276.SH', '恒瑞医药'), ('000568.SZ', '泸州老窖'), ('601888.SH', '中国中免'),
        ('002415.SZ', '海康威视'), ('600309.SH', '万华化学'), ('000002.SZ', '万科A'),
        ('601398.SH', '工商银行'), ('600887.SH', '伊利股份'), ('600438.SH', '通威股份'),
        ('002142.SZ', '宁波银行'), ('300059.SZ', '东方财富'), ('601166.SH', '兴业银行'),
        ('002475.SZ', '立讯精密'), ('601288.SH', '农业银行'), ('600030.SH', '中信证券'),
        ('603288.SH', '海天味业'), ('601668.SH', '中国建筑'), ('000001.SZ', '平安银行'),
        ('601088.SH', '中国神华'), ('000651.SZ', '格力电器'), ('600809.SH', '山西汾酒'),
        ('601899.SH', '紫金矿业'), ('300124.SZ', '汇川技术'), ('002352.SZ', '顺丰控股'),
        ('601985.SH', '中国核电'), ('600031.SH', '三一重工'), ('600436.SH', '片仔癀'),
        ('300274.SZ', '阳光电源'), ('601939.SH', '建设银行'), ('002812.SZ', '恩捷股份'),
        ('600585.SH', '海螺水泥'), ('603501.SH', '韦尔股份'), ('000725.SZ', '京东方A'),
        ('601628.SH', '中国人寿'), ('600000.SH', '浦发银行'), ('002714.SZ', '牧原股份'),
        ('002230.SZ', '科大讯飞'), ('603986.SH', '兆易创新'), ('601138.SH', '工业富联'),
        ('600104.SH', '上汽集团'), ('601601.SH', '中国太保'),
    ]
    
    # 取前top_n只
    selected_stocks = STOCK_POOL[:top_n]
    
    stocks_df = pd.DataFrame(selected_stocks, columns=['ts_code', 'name'])
    
    print(f"成功准备 {len(stocks_df)} 只股票")
    return stocks_df


def get_stock_data(pro, ts_code, start_date, end_date):
    """
    获取股票日线数据
    
    参数:
        pro: Tushare API 对象
        ts_code: 股票代码
        start_date: 开始日期 (YYYYMMDD)
        end_date: 结束日期 (YYYYMMDD)
    
    返回:
        DataFrame: 包含 OHLCV 数据
    """
    try:
        # 添加延时避免触发API限制
        time.sleep(API_CALL_DELAY)
        
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or len(df) == 0:
            return None
        
        # 按日期排序
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        df.set_index('trade_date', inplace=True)
        
        return df[['open', 'high', 'low', 'close', 'vol']].rename(columns={'vol': 'volume'})
    except Exception as e:
        print(f"  警告: 获取 {ts_code} 数据失败: {e}")
        return None


# ==================== 2. MACD 指标计算 ====================
def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    
    参数:
        df: 包含收盘价的数据框
        fast: 快线周期，默认12
        slow: 慢线周期，默认26
        signal: 信号线周期，默认9
    
    返回:
        DataFrame: 添加了MACD相关列
    """
    # 计算EMA
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # DIF (快线)
    df['DIF'] = ema_fast - ema_slow
    
    # DEA (慢线/信号线)
    df['DEA'] = df['DIF'].ewm(span=signal, adjust=False).mean()
    
    # MACD柱状图
    df['MACD'] = (df['DIF'] - df['DEA']) * 2
    
    # 金叉死叉信号
    df['golden_cross'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    df['death_cross'] = (df['DIF'] < df['DEA']) & (df['DIF'].shift(1) >= df['DEA'].shift(1))
    
    return df


# ==================== 3. 回测策略 ====================
def backtest_macd_strategy(df, index_df=None, initial_capital=150000):
    """
    MACD金叉死叉策略回测
    
    策略规则：
    - 金叉（DIF上穿DEA）：全仓买入
    - 死叉（DIF下穿DEA）：全仓卖出
    
    参数:
        df: 包含MACD指标的数据框
        index_df: 指数数据（用于计算阿尔法、贝塔）
        initial_capital: 初始资金
    
    返回:
        dict: 回测结果统计
    """
    if df is None or len(df) == 0:
        return None
    
    # 初始化
    capital = initial_capital  # 现金
    position = 0  # 持仓股数
    position_value = 0  # 持仓市值
    total_value = initial_capital  # 总资产
    trades = []  # 交易记录
    
    # 每日记录
    daily_records = []
    
    for i, (date, row) in enumerate(df.iterrows()):
        price = row['close']
        
        # 金叉买入
        if row['golden_cross'] and capital > 0:
            position = int(capital / price / 100) * 100  # 整手买入
            if position > 0:
                cost = position * price
                capital -= cost
                trades.append({
                    'date': date,
                    'action': '买入',
                    'price': price,
                    'shares': position,
                    'amount': cost
                })
        
        # 死叉卖出
        elif row['death_cross'] and position > 0:
            revenue = position * price
            capital += revenue
            trades.append({
                'date': date,
                'action': '卖出',
                'price': price,
                'shares': position,
                'amount': revenue,
                'profit': revenue - sum([t['amount'] for t in trades if t['action'] == '买入'][-1:])
            })
            position = 0
        
        # 计算当日总资产
        position_value = position * price
        total_value = capital + position_value
        
        daily_records.append({
            'date': date,
            'close': price,
            'capital': capital,
            'position': position,
            'position_value': position_value,
            'total_value': total_value,
            'DIF': row['DIF'],
            'DEA': row['DEA'],
            'MACD': row['MACD'],
            'golden_cross': row['golden_cross'],
            'death_cross': row['death_cross']
        })
    
    # 最后一天，如果有持仓则按收盘价结算
    if position > 0:
        final_price = df['close'].iloc[-1]
        position_value = position * final_price
        total_value = capital + position_value
    
    # 转换为DataFrame
    records_df = pd.DataFrame(daily_records)
    records_df.set_index('date', inplace=True)
    
    # 计算收益率
    records_df['daily_return'] = records_df['total_value'].pct_change()
    records_df['cumulative_return'] = (records_df['total_value'] / initial_capital) - 1
    
    # 计算统计指标
    total_return = (total_value - initial_capital) / initial_capital
    
    # 年化收益率
    trading_days = len(df)
    annualized_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
    
    # 波动率（年化）
    daily_volatility = records_df['daily_return'].std()
    annualized_volatility = daily_volatility * np.sqrt(252)
    
    # 无风险利率
    risk_free_rate = 0.03
    
    # 夏普比率
    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else 0
    
    # 最大回撤
    records_df['peak'] = records_df['total_value'].cummax()
    records_df['drawdown'] = (records_df['total_value'] - records_df['peak']) / records_df['peak']
    max_drawdown = records_df['drawdown'].min()
    
    # 交易次数
    buy_count = len([t for t in trades if t['action'] == '买入'])
    sell_count = len([t for t in trades if t['action'] == '卖出'])
    
    # 计算阿尔法和贝塔
    alpha = None
    beta = None
    
    if index_df is not None and len(index_df) > 0:
        # 合并策略收益和指数收益
        merged = records_df[['daily_return']].join(index_df[['index_return']], how='inner')
        merged = merged.dropna()
        
        if len(merged) > 30:  # 至少需要30个数据点
            # 计算贝塔（策略收益对指数收益的回归系数）
            cov_matrix = np.cov(merged['daily_return'], merged['index_return'])
            if cov_matrix.shape == (2, 2):
                beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else 0
                
                # 计算阿尔法（超额收益）
                # Jensen's Alpha = 策略收益 - (无风险利率 + 贝塔 * (市场收益 - 无风险利率))
                strategy_annual_return = annualized_return
                index_annual_return = ((1 + merged['index_return'].mean()) ** 252) - 1
                alpha = strategy_annual_return - (risk_free_rate + beta * (index_annual_return - risk_free_rate))
    
    return {
        'initial_capital': initial_capital,
        'final_value': total_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_volatility,
        'sharpe_ratio': sharpe_ratio,
        'alpha': alpha,
        'beta': beta,
        'max_drawdown': max_drawdown,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'trades': trades,
        'records': records_df
    }


# ==================== 4. 可视化 ====================
def plot_backtest_results(df, result, stock_code, stock_name=''):
    """
    绘制回测结果图表
    
    参数:
        df: 股票数据
        result: 回测结果
        stock_code: 股票代码
        stock_name: 股票名称
    """
    fig, axes = plt.subplots(4, 1, figsize=(16, 14), gridspec_kw={'height_ratios': [2, 1, 1, 1]})
    
    records = result['records']
    trades = result['trades']
    name_str = f" ({stock_name})" if stock_name else ""
    
    # 1. 价格和买卖点
    ax1 = axes[0]
    ax1.plot(records.index, records['close'], label='收盘价', color='black', linewidth=1)
    
    # 标记买入点
    buy_trades = [t for t in trades if t['action'] == '买入']
    if buy_trades:
        buy_dates = [t['date'] for t in buy_trades]
        buy_prices = [t['price'] for t in buy_trades]
        ax1.scatter(buy_dates, buy_prices, marker='^', color='red', s=100, label='买入', zorder=5)
    
    # 标记卖出点
    sell_trades = [t for t in trades if t['action'] == '卖出']
    if sell_trades:
        sell_dates = [t['date'] for t in sell_trades]
        sell_prices = [t['price'] for t in sell_trades]
        ax1.scatter(sell_dates, sell_prices, marker='v', color='green', s=100, label='卖出', zorder=5)
    
    ax1.set_ylabel('价格 (元)')
    ax1.set_title(f'{stock_code}{name_str} - MACD策略回测')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. MACD指标
    ax2 = axes[1]
    ax2.plot(records.index, records['DIF'], label='DIF', color='blue', linewidth=1)
    ax2.plot(records.index, records['DEA'], label='DEA', color='orange', linewidth=1)
    
    # MACD柱状图
    macd_colors = ['red' if v >= 0 else 'green' for v in records['MACD']]
    ax2.bar(records.index, records['MACD'], color=macd_colors, alpha=0.5, width=1)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # 标记金叉死叉
    golden_crosses = records[records['golden_cross']].index
    death_crosses = records[records['death_cross']].index
    ax2.scatter(golden_crosses, records.loc[golden_crosses, 'DIF'], 
                marker='^', color='red', s=50, zorder=5)
    ax2.scatter(death_crosses, records.loc[death_crosses, 'DIF'], 
                marker='v', color='green', s=50, zorder=5)
    
    ax2.set_ylabel('MACD')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # 3. 资金曲线
    ax3 = axes[2]
    ax3.plot(records.index, records['total_value'], label='策略资金曲线', 
             color='blue', linewidth=1.5)
    ax3.axhline(y=result['initial_capital'], color='gray', linestyle='--', 
                label='初始资金', alpha=0.7)
    
    # 添加最终收益标注
    final_return_pct = result['total_return'] * 100
    color = 'green' if final_return_pct >= 0 else 'red'
    ax3.text(0.02, 0.95, f'总收益率: {final_return_pct:.2f}%', 
             transform=ax3.transAxes, fontsize=12, fontweight='bold',
             verticalalignment='top', color=color,
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 添加阿尔法和贝塔标注
    if result['alpha'] is not None and result['beta'] is not None:
        ax3.text(0.02, 0.85, f'Alpha: {result["alpha"]*100:.2f}%  Beta: {result["beta"]:.2f}', 
                 transform=ax3.transAxes, fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    ax3.set_ylabel('资产价值 (元)')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    
    # 4. 回撤
    ax4 = axes[3]
    ax4.fill_between(records.index, records['drawdown'] * 100, 0, 
                      color='red', alpha=0.3, label='回撤')
    ax4.plot(records.index, records['drawdown'] * 100, color='red', linewidth=1)
    ax4.set_ylabel('回撤 (%)')
    ax4.set_xlabel('日期')
    ax4.legend(loc='lower left')
    ax4.grid(True, alpha=0.3)
    
    # 添加最大回撤标注
    max_dd_pct = result['max_drawdown'] * 100
    ax4.text(0.02, 0.05, f'最大回撤: {max_dd_pct:.2f}%', 
             transform=ax4.transAxes, fontsize=10, fontweight='bold',
             verticalalignment='bottom', color='red',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    safe_code = stock_code.replace(".", "_")
    plt.savefig(f'week_1/{safe_code}_MACD回测.png', dpi=150, bbox_inches='tight')
    print(f"图表已保存: week_1/{safe_code}_MACD回测.png")
    plt.close()


# ==================== 5. 主程序 ====================
def main():
    print("=" * 70)
    print(f"MACD金叉死叉策略回测 - 沪深300市值前{TOP_N_STOCKS}只股票")
    print("=" * 70)
    print(f"\n策略参数:")
    print(f"  - 回测时间: {START_DATE} 至 {END_DATE} (近两年)")
    print(f"  - 每只股票初始资金: {INITIAL_CAPITAL_PER_STOCK:,} 元")
    print(f"  - 买入信号: MACD金叉 (DIF上穿DEA)")
    print(f"  - 卖出信号: MACD死叉 (DIF下穿DEA)")
    print(f"  - 无风险利率: 3% (用于计算夏普比率)")
    
    try:
        # 初始化 Tushare
        print("\n【1/5】初始化 Tushare API...")
        pro = init_tushare()
        print("API 连接成功")
        
        # 获取沪深300市值前N股票
        print(f"\n【2/5】获取沪深300市值前{TOP_N_STOCKS}股票...")
        stocks_df = get_hs300_stocks(pro, top_n=TOP_N_STOCKS)
        stock_codes = stocks_df['ts_code'].tolist()
        stock_names = dict(zip(stocks_df['ts_code'], stocks_df['name']))
        print(f"成功获取 {len(stock_codes)} 只股票")
        
        # 注意：由于Token权限限制(120积分)，无法使用index_daily接口
        # Alpha和Beta指标将无法计算
        index_df = None
        print("\n【3/5】注意: 当前Token权限只能使用daily接口，Alpha/Beta指标将无法计算")
        
        # 回测统计
        all_results = []
        
        print("\n【4/5】开始回测...")
        print("-" * 70)
        
        for i, ts_code in enumerate(stock_codes):
            print(f"\n[{i+1}/{len(stock_codes)}] 回测 {ts_code} ({stock_names.get(ts_code, '')})...")
            
            # 获取数据
            df = get_stock_data(pro, ts_code, START_DATE, END_DATE)
            if df is None or len(df) < 60:  # 至少需要60天数据
                print(f"  警告: 数据不足，跳过")
                continue
            
            # 计算MACD
            df = calculate_macd(df)
            
            # 回测
            result = backtest_macd_strategy(df, index_df, INITIAL_CAPITAL_PER_STOCK)
            if result is None:
                continue
            
            all_results.append({
                'ts_code': ts_code,
                'name': stock_names.get(ts_code, ''),
                'result': result
            })
            
            print(f"  总收益率: {result['total_return']*100:.2f}%")
            print(f"  年化收益率: {result['annualized_return']*100:.2f}%")
            print(f"  年化波动率: {result['annualized_volatility']*100:.2f}%")
            print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
            print(f"  最大回撤: {result['max_drawdown']*100:.2f}%")
            print(f"  交易次数: 买入{result['buy_count']}次 / 卖出{result['sell_count']}次")
            
            # 绘制图表(只绘制前5只股票的详细图表)
            if i < 5:
                plot_backtest_results(df, result, ts_code, stock_names.get(ts_code, ''))
        
        # 汇总统计
        print("\n" + "=" * 70)
        print("【5/5】汇总统计")
        print("=" * 70)
        
        if len(all_results) == 0:
            print("错误: 没有成功的回测结果")
            return
        
        # 计算汇总指标
        total_returns = [r['result']['total_return'] for r in all_results]
        annualized_returns = [r['result']['annualized_return'] for r in all_results]
        volatilities = [r['result']['annualized_volatility'] for r in all_results]
        sharpe_ratios = [r['result']['sharpe_ratio'] for r in all_results]
        alphas = [r['result']['alpha'] for r in all_results if r['result']['alpha'] is not None]
        betas = [r['result']['beta'] for r in all_results if r['result']['beta'] is not None]
        max_drawdowns = [r['result']['max_drawdown'] for r in all_results]
        
        # 等权重投资组合收益
        avg_return = np.mean(total_returns)
        avg_annual_return = np.mean(annualized_returns)
        avg_volatility = np.mean(volatilities)
        avg_sharpe = np.mean(sharpe_ratios)
        avg_alpha = np.mean(alphas) if alphas else None
        avg_beta = np.mean(betas) if betas else None
        avg_max_dd = np.mean(max_drawdowns)
        
        # 总资金统计
        total_initial = len(all_results) * INITIAL_CAPITAL_PER_STOCK
        total_final = sum([r['result']['final_value'] for r in all_results])
        portfolio_return = (total_final - total_initial) / total_initial
        
        print(f"\n回测股票数量: {len(all_results)} 只")
        print(f"总初始资金: {total_initial:,.0f} 元")
        print(f"总最终资金: {total_final:,.0f} 元")
        print(f"\n整体收益率: {portfolio_return*100:.2f}%")
        print(f"平均年化收益率: {avg_annual_return*100:.2f}%")
        print(f"平均年化波动率: {avg_volatility*100:.2f}%")
        print(f"平均夏普比率: {avg_sharpe:.2f}")
        if avg_alpha is not None:
            print(f"平均Alpha: {avg_alpha*100:.2f}%")
            print(f"平均Beta: {avg_beta:.2f}")
        print(f"平均最大回撤: {avg_max_dd*100:.2f}%")
        
        # 分布统计
        print(f"\n收益率分布:")
        print(f"  最高: {max(total_returns)*100:.2f}%")
        print(f"  最低: {min(total_returns)*100:.2f}%")
        print(f"  中位数: {np.median(total_returns)*100:.2f}%")
        print(f"  正收益股票数: {sum([1 for r in total_returns if r > 0])} / {len(total_returns)}")
        
        print(f"\n夏普比率分布:")
        print(f"  最高: {max(sharpe_ratios):.2f}")
        print(f"  最低: {min(sharpe_ratios):.2f}")
        print(f"  正夏普比率: {sum([1 for s in sharpe_ratios if s > 0])} / {len(sharpe_ratios)}")
        
        if alphas:
            print(f"\nAlpha分布:")
            print(f"  最高: {max(alphas)*100:.2f}%")
            print(f"  最低: {min(alphas)*100:.2f}%")
            print(f"  正Alpha: {sum([1 for a in alphas if a > 0])} / {len(alphas)}")
            
            print(f"\nBeta分布:")
            print(f"  最高: {max(betas):.2f}")
            print(f"  最低: {min(betas):.2f}")
            print(f"  Beta > 1 (激进): {sum([1 for b in betas if b > 1])} / {len(betas)}")
            print(f"  Beta < 1 (保守): {sum([1 for b in betas if b < 1])} / {len(betas)}")
        
        # 绘制汇总图表
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # 收益率分布
        ax1 = axes[0, 0]
        ax1.hist([r*100 for r in total_returns], bins=15, alpha=0.7, color='steelblue', edgecolor='black')
        ax1.axvline(avg_return*100, color='red', linestyle='--', linewidth=2, label=f'均值: {avg_return*100:.2f}%')
        ax1.axvline(0, color='black', linestyle='-', linewidth=0.5)
        ax1.set_xlabel('总收益率 (%)')
        ax1.set_ylabel('股票数量')
        ax1.set_title('总收益率分布')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 夏普比率分布
        ax2 = axes[0, 1]
        ax2.hist(sharpe_ratios, bins=15, alpha=0.7, color='green', edgecolor='black')
        ax2.axvline(avg_sharpe, color='red', linestyle='--', linewidth=2, label=f'均值: {avg_sharpe:.2f}')
        ax2.axvline(0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_xlabel('夏普比率')
        ax2.set_ylabel('股票数量')
        ax2.set_title('夏普比率分布')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 收益率 vs 波动率 散点图
        ax3 = axes[0, 2]
        scatter = ax3.scatter([v*100 for v in volatilities], [r*100 for r in annualized_returns], 
                              c=sharpe_ratios, cmap='RdYlGn', alpha=0.7, s=50)
        ax3.axhline(0, color='black', linestyle='-', linewidth=0.5)
        ax3.axvline(0, color='black', linestyle='-', linewidth=0.5)
        ax3.set_xlabel('年化波动率 (%)')
        ax3.set_ylabel('年化收益率 (%)')
        ax3.set_title('收益率 vs 波动率 (颜色=夏普比率)')
        plt.colorbar(scatter, ax=ax3, label='夏普比率')
        ax3.grid(True, alpha=0.3)
        
        # 最大回撤分布
        ax4 = axes[1, 0]
        ax4.hist([m*100 for m in max_drawdowns], bins=15, alpha=0.7, color='coral', edgecolor='black')
        ax4.axvline(avg_max_dd*100, color='red', linestyle='--', linewidth=2, label=f'均值: {avg_max_dd*100:.2f}%')
        ax4.set_xlabel('最大回撤 (%)')
        ax4.set_ylabel('股票数量')
        ax4.set_title('最大回撤分布')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Alpha分布
        if alphas:
            ax5 = axes[1, 1]
            ax5.hist([a*100 for a in alphas], bins=15, alpha=0.7, color='purple', edgecolor='black')
            if avg_alpha is not None:
                ax5.axvline(avg_alpha*100, color='red', linestyle='--', linewidth=2, label=f'均值: {avg_alpha*100:.2f}%')
            ax5.axvline(0, color='black', linestyle='-', linewidth=0.5)
            ax5.set_xlabel('Alpha (%)')
            ax5.set_ylabel('股票数量')
            ax5.set_title('Alpha分布 (相对于沪深300)')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
            
            # Beta分布
            ax6 = axes[1, 2]
            ax6.hist(betas, bins=15, alpha=0.7, color='orange', edgecolor='black')
            if avg_beta is not None:
                ax6.axvline(avg_beta, color='red', linestyle='--', linewidth=2, label=f'均值: {avg_beta:.2f}')
            ax6.axvline(1, color='black', linestyle='-', linewidth=0.5, label='Beta=1')
            ax6.set_xlabel('Beta')
            ax6.set_ylabel('股票数量')
            ax6.set_title('Beta分布 (相对于沪深300)')
            ax6.legend()
            ax6.grid(True, alpha=0.3)
        else:
            ax5 = axes[1, 1]
            ax5.text(0.5, 0.5, 'Alpha数据不可用', ha='center', va='center', fontsize=14)
            ax5.set_xticks([])
            ax5.set_yticks([])
            
            ax6 = axes[1, 2]
            ax6.text(0.5, 0.5, 'Beta数据不可用', ha='center', va='center', fontsize=14)
            ax6.set_xticks([])
            ax6.set_yticks([])
        
        plt.tight_layout()
        plt.savefig('week_1/MACD策略_汇总统计.png', dpi=150, bbox_inches='tight')
        print(f"\n汇总图表已保存: week_1/MACD策略_汇总统计.png")
        plt.close()
        
        # 输出最佳和最差股票
        print("\n" + "-" * 70)
        print("表现最佳的前5只股票:")
        sorted_results = sorted(all_results, key=lambda x: x['result']['total_return'], reverse=True)
        for i, r in enumerate(sorted_results[:5]):
            print(f"  {i+1}. {r['ts_code']} ({r['name']}): {r['result']['total_return']*100:.2f}%")
        
        print("\n表现最差的前5只股票:")
        for i, r in enumerate(sorted_results[-5:]):
            print(f"  {i+1}. {r['ts_code']} ({r['name']}): {r['result']['total_return']*100:.2f}%")
        
        print("\n回测完成！")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
