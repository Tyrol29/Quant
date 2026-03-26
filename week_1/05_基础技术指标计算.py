"""
Week 1 - 基础金融指标计算教程
===========================
本文件演示以下核心指标的计算方法：
1. 极差 (Range)
2. 成交量加权平均价格 (VWAP)
3. 收益率 (Returns)
4. 波动率 (Volatility)
5. 年化波动率 (Annualized Volatility)
6. 月度波动率 (Monthly Volatility)

作者: 量化学习笔记
日期: 2026-03-26
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tushare as ts

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# ==================== 1. 创建示例数据 ====================
def create_sample_data():
    """
    创建模拟的股票日线数据用于演示
    """
    np.random.seed(42)  # 固定随机种子，结果可复现
    
    # 生成30个交易日的数据
    dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
    
    # 模拟价格走势（随机游走）
    initial_price = 100
    returns = np.random.normal(0.001, 0.02, len(dates))  # 日均收益0.1%，波动2%
    prices = initial_price * (1 + returns).cumprod()
    
    # 生成OHLC数据
    data = {
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
        'high': prices * (1 + np.abs(np.random.normal(0.01, 0.005, len(dates)))),
        'low': prices * (1 - np.abs(np.random.normal(0.01, 0.005, len(dates)))),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, len(dates))
    }
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    
    # 确保 high >= open, close, low
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    return df


# ==================== 2. 极差 (Range) ====================
def calculate_range(df):
    """
    极差 (Range): 当日最高价与最低价的差值
    
    公式: Range = High - Low
    
    意义:
    - 反映当日价格波动幅度
    - 极差扩大表示波动加剧，可能伴随重要消息或趋势转折
    - 极差收窄表示市场观望，可能即将变盘
    
    参数:
        df: DataFrame包含 'high' 和 'low' 列
    
    返回:
        Series: 每日极差值
    """
    df['range'] = df['high'] - df['low']
    
    # 计算极差的一些统计指标
    range_stats = {
        'mean_range': df['range'].mean(),      # 平均极差
        'max_range': df['range'].max(),        # 最大极差
        'min_range': df['range'].min(),        # 最小极差
        'range_ratio': (df['range'] / df['close']).mean()  # 极差占收盘价比例
    }
    
    return df['range'], range_stats


# ==================== 3. 成交量加权平均价格 (VWAP) ====================
def calculate_vwap(df):
    """
    VWAP (Volume Weighted Average Price): 成交量加权平均价格
    
    公式: VWAP = Σ(典型价格 × 成交量) / Σ(成交量)
         其中典型价格 = (High + Low + Close) / 3
    
    意义:
    - 机构投资者常用，表示"公允价格"
    - 价格高于VWAP，说明买盘强劲；低于VWAP，卖盘占优
    - 常用于算法交易拆单，减少市场冲击
    
    参数:
        df: DataFrame包含 'high', 'low', 'close', 'volume' 列
    
    返回:
        Series: 每日VWAP值
    """
    # 计算典型价格 (Typical Price)
    tp = (df['high'] + df['low'] + df['close']) / 3
    
    # 计算VWAP
    df['vwap'] = (tp * df['volume']).cumsum() / df['volume'].cumsum()
    
    # 当日VWAP（日内交易用）
    df['vwap_daily'] = tp  # 简化版，实际日内需要逐笔数据
    
    return df['vwap']


# ==================== 4. 收益率 (Returns) ====================
def calculate_returns(df):
    """
    收益率计算: 衡量投资回报的核心指标
    
    两种计算方法:
    
    1. 简单收益率 (Simple Return):
       R_t = (P_t - P_{t-1}) / P_{t-1} = P_t / P_{t-1} - 1
       
    2. 对数收益率 (Log Return):
       r_t = ln(P_t / P_{t-1})
    
    对数收益率的优势:
    - 时间可加性: 多期对数收益率 = 各期对数收益率之和
    - 数值范围对称，更适合统计分析
    - 波动率计算时更准确
    
    参数:
        df: DataFrame包含 'close' 列
    
    返回:
        DataFrame: 包含各种收益率列
    """
    # 简单收益率
    df['simple_return'] = df['close'].pct_change()
    
    # 对数收益率
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # 累计收益率
    df['cumulative_return'] = (1 + df['simple_return']).cumprod() - 1
    
    # 对数累计收益率
    df['cumulative_log_return'] = df['log_return'].cumsum()
    
    return df[['simple_return', 'log_return', 'cumulative_return', 'cumulative_log_return']]


# ==================== 5. 波动率 (Volatility) ====================
def calculate_volatility(df, window=20):
    """
    波动率 (Volatility): 衡量价格波动幅度的风险指标
    
    计算方法:
    - 日波动率 = 收益率的标准差
    - 通常使用对数收益率计算更准确
    
    公式: 
        σ = sqrt(Σ(r_i - r_mean)² / (n-1))
    
    参数:
        df: DataFrame包含收益率列
        window: 滚动窗口大小，默认20日（一个月交易日）
    
    返回:
        DataFrame: 包含各种波动率指标
    """
    # 计算对数收益率（如未计算）
    if 'log_return' not in df.columns:
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # 滚动波动率（日波动率）
    df['daily_volatility'] = df['log_return'].rolling(window=window).std()
    
    # 年化波动率 (假设一年252个交易日)
    trading_days_per_year = 252
    df['annual_volatility'] = df['daily_volatility'] * np.sqrt(trading_days_per_year)
    
    # 月度波动率 (假设一月21个交易日)
    trading_days_per_month = 21
    df['monthly_volatility'] = df['daily_volatility'] * np.sqrt(trading_days_per_month)
    
    # 波动率的统计特征
    vol_stats = {
        'current_daily_vol': df['daily_volatility'].iloc[-1],
        'current_annual_vol': df['annual_volatility'].iloc[-1],
        'avg_annual_vol': df['annual_volatility'].mean(),
        'vol_of_vol': df['daily_volatility'].std()  # 波动率的波动率
    }
    
    return df[['daily_volatility', 'annual_volatility', 'monthly_volatility']], vol_stats


# ==================== 6. 综合计算函数 ====================
def calculate_all_indicators(df):
    """
    计算所有技术指标的整合函数
    
    参数:
        df: 包含OHLCV数据的DataFrame
    
    返回:
        DataFrame: 包含所有计算指标的完整数据
        dict: 各项统计指标汇总
    """
    stats = {}
    
    # 1. 计算极差
    df['range'], range_stats = calculate_range(df)
    stats['极差统计'] = range_stats
    
    # 2. 计算VWAP
    df['vwap'] = calculate_vwap(df)
    
    # 3. 计算收益率
    returns_df = calculate_returns(df)
    for col in returns_df.columns:
        df[col] = returns_df[col]
    
    # 4. 计算波动率
    vol_df, vol_stats = calculate_volatility(df)
    for col in vol_df.columns:
        df[col] = vol_df[col]
    stats['波动率统计'] = vol_stats
    
    return df, stats


# ==================== 7. 可视化函数 ====================
def plot_indicators(df):
    """
    可视化各项指标
    """
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    
    # 1. 价格与极差
    ax1 = axes[0, 0]
    ax1_twin = ax1.twinx()
    ax1.plot(df.index, df['close'], label='收盘价', color='blue')
    ax1_twin.bar(df.index, df['range'], alpha=0.3, label='极差', color='orange')
    ax1.set_title('收盘价与极差')
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    
    # 2. VWAP对比
    ax2 = axes[0, 1]
    ax2.plot(df.index, df['close'], label='收盘价', color='blue')
    ax2.plot(df.index, df['vwap'], label='VWAP', color='red', linestyle='--')
    ax2.set_title('收盘价 vs VWAP')
    ax2.legend()
    
    # 3. 收益率分布
    ax3 = axes[1, 0]
    ax3.hist(df['simple_return'].dropna(), bins=20, alpha=0.7, edgecolor='black')
    ax3.axvline(df['simple_return'].mean(), color='red', linestyle='--', label=f'均值: {df["simple_return"].mean():.4f}')
    ax3.set_title('日收益率分布')
    ax3.set_xlabel('收益率')
    ax3.set_ylabel('频次')
    ax3.legend()
    
    # 4. 累计收益
    ax4 = axes[1, 1]
    ax4.plot(df.index, df['cumulative_return'] * 100, label='累计收益率(%)', color='green')
    ax4.fill_between(df.index, 0, df['cumulative_return'] * 100, alpha=0.3)
    ax4.set_title('累计收益率')
    ax4.set_ylabel('收益率 (%)')
    ax4.legend()
    
    # 5. 波动率走势
    ax5 = axes[2, 0]
    ax5.plot(df.index, df['daily_volatility'], label='日波动率', color='purple')
    ax5.set_title('滚动波动率 (20日)')
    ax5.legend()
    
    # 6. 年化波动率
    ax6 = axes[2, 1]
    ax6.plot(df.index, df['annual_volatility'] * 100, label='年化波动率(%)', color='red')
    ax6.axhline(20, color='gray', linestyle='--', alpha=0.5, label='20%参考线')
    ax6.set_title('年化波动率')
    ax6.set_ylabel('波动率 (%)')
    ax6.legend()
    
    plt.tight_layout()
    plt.savefig('week_1/技术指标可视化.png', dpi=150)
    print("\n图表已保存至: week_1/技术指标可视化.png")
    plt.show()


# ==================== 8. 主程序 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("基础金融指标计算演示")
    print("=" * 60)
    
    # 创建示例数据
    print("\n【步骤1】创建模拟股票数据...")
    df = create_sample_data()
    print(f"数据范围: {df.index[0].date()} 至 {df.index[-1].date()}")
    print(f"数据条数: {len(df)} 条")
    print("\n原始数据预览:")
    print(df.head())
    
    # 计算所有指标
    print("\n" + "=" * 60)
    print("【步骤2】计算各项技术指标...")
    print("=" * 60)
    
    df, stats = calculate_all_indicators(df)
    
    # 显示完整数据
    print("\n计算结果预览 (前5行):")
    print(df[['open', 'high', 'low', 'close', 'range', 'vwap', 
              'simple_return', 'daily_volatility', 'annual_volatility']].head())
    
    # 显示统计结果
    print("\n" + "=" * 60)
    print("【步骤3】统计指标汇总")
    print("=" * 60)
    
    print("\n📊 极差 (Range) 统计:")
    for key, value in stats['极差统计'].items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.4f}")
        else:
            print(f"  - {key}: {value}")
    
    print("\n📈 波动率 (Volatility) 统计:")
    for key, value in stats['波动率统计'].items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.4f} ({value*100:.2f}%)")
        else:
            print(f"  - {key}: {value}")
    
    # 关键指标解释
    print("\n" + "=" * 60)
    print("【关键指标解读】")
    print("=" * 60)
    
    latest = df.iloc[-1]
    print(f"""
当前最新数据 ({df.index[-1].date()}):
  收盘价: {latest['close']:.2f}
  当日极差: {latest['range']:.2f} ({latest['range']/latest['close']*100:.2f}%)
  VWAP: {latest['vwap']:.2f}
  最新日收益率: {latest['simple_return']*100:.2f}%
  20日年化波动率: {latest['annual_volatility']*100:.2f}%
  
波动率水平判断:
  {'⚠️ 波动率较低 (<10%)' if latest['annual_volatility'] < 0.1 else 
   '✅ 波动率正常 (10%-30%)' if latest['annual_volatility'] < 0.3 else 
   '🔥 波动率较高 (>30%)'}
""")
    
    # 可视化
    print("=" * 60)
    print("【步骤4】生成可视化图表...")
    print("=" * 60)
    plot_indicators(df)
    
    print("\n✅ 所有计算完成！")
    print("\n提示:")
    print("1. 本示例使用模拟数据，实际应用时请替换为真实股票数据")
    print("2. 可以使用 AKShare 获取真实A股数据: akshare.stock_zh_a_hist()")
    print("3. 波动率计算建议使用对数收益率，统计性质更好")
