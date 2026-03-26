"""
Week 1 - 使用 Tushare 真实股票数据计算技术指标
===============================================
本文件演示：
1. 使用 Tushare API 获取真实股票数据
2. 计算极差、VWAP、收益率、波动率等指标
3. 可视化分析

依赖安装：
    pip install tushare pandas numpy matplotlib

API Token: 877cd5e05fb5edf3115e7a26e16741c4333d07a1216168bde06e781c
"""

import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta

# ==================== 配置 ====================
TUSHARE_TOKEN = "877cd5e05fb5edf3115e7a26e16741c4333d07a1216168bde06e781c"

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 常见股票代码池（沪深300成分股中的部分，120积分可直接访问daily接口）
STOCK_POOL = [
    ('000001.SZ', '平安银行'),
    ('000002.SZ', '万科A'),
    ('000063.SZ', '中兴通讯'),
    ('000100.SZ', 'TCL科技'),
    ('000333.SZ', '美的集团'),
    ('000538.SZ', '云南白药'),
    ('000568.SZ', '泸州老窖'),
    ('000651.SZ', '格力电器'),
    ('000725.SZ', '京东方A'),
    ('000768.SZ', '中航西飞'),
    ('000858.SZ', '五粮液'),
    ('000895.SZ', '双汇发展'),
    ('002001.SZ', '新和成'),
    ('002007.SZ', '华兰生物'),
    ('002024.SZ', '苏宁易购'),
    ('002027.SZ', '分众传媒'),
    ('002049.SZ', '紫光国微'),
    ('002120.SZ', '韵达股份'),
    ('002142.SZ', '宁波银行'),
    ('002230.SZ', '科大讯飞'),
    ('002271.SZ', '东方雨虹'),
    ('002304.SZ', '洋河股份'),
    ('002352.SZ', '顺丰控股'),
    ('002415.SZ', '海康威视'),
    ('002460.SZ', '赣锋锂业'),
    ('002475.SZ', '立讯精密'),
    ('002594.SZ', '比亚迪'),
    ('002714.SZ', '牧原股份'),
    ('002812.SZ', '恩捷股份'),
    ('003816.SZ', '中国广核'),
    ('300003.SZ', '乐普医疗'),
    ('300014.SZ', '亿纬锂能'),
    ('300015.SZ', '爱尔眼科'),
    ('300033.SZ', '同花顺'),
    ('300059.SZ', '东方财富'),
    ('300122.SZ', '智飞生物'),
    ('300124.SZ', '汇川技术'),
    ('300142.SZ', '沃森生物'),
    ('300274.SZ', '阳光电源'),
    ('300408.SZ', '三环集团'),
    ('300413.SZ', '芒果超媒'),
    ('300433.SZ', '蓝思科技'),
    ('300498.SZ', '温氏股份'),
    ('300750.SZ', '宁德时代'),
    ('600000.SH', '浦发银行'),
    ('600009.SH', '上海机场'),
    ('600010.SH', '包钢股份'),
    ('600016.SH', '民生银行'),
    ('600028.SH', '中国石化'),
    ('600030.SH', '中信证券'),
    ('600031.SH', '三一重工'),
    ('600036.SH', '招商银行'),
    ('600048.SH', '保利地产'),
    ('600050.SH', '中国联通'),
    ('600104.SH', '上汽集团'),
    ('600196.SH', '复星医药'),
    ('600276.SH', '恒瑞医药'),
    ('600309.SH', '万华化学'),
    ('600340.SH', '华夏幸福'),
    ('600346.SH', '恒力石化'),
    ('600406.SH', '国电南瑞'),
    ('600436.SH', '片仔癀'),
    ('600438.SH', '通威股份'),
    ('600519.SH', '贵州茅台'),
    ('600547.SH', '山东黄金'),
    ('600570.SH', '恒生电子'),
    ('600585.SH', '海螺水泥'),
    ('600588.SH', '用友网络'),
    ('600600.SH', '青岛啤酒'),
    ('600660.SH', '福耀玻璃'),
    ('600690.SH', '海尔智家'),
    ('600703.SH', '三安光电'),
    ('600745.SH', '闻泰科技'),
    ('600809.SH', '山西汾酒'),
    ('600837.SH', '海通证券'),
    ('600887.SH', '伊利股份'),
    ('600893.SH', '航发动力'),
    ('600900.SH', '长江电力'),
    ('601012.SH', '隆基绿能'),
    ('601066.SH', '中信建投'),
    ('601088.SH', '中国神华'),
    ('601111.SH', '中国国航'),
    ('601138.SH', '工业富联'),
    ('601166.SH', '兴业银行'),
    ('601169.SH', '北京银行'),
    ('601186.SH', '中国铁建'),
    ('601211.SH', '国泰君安'),
    ('601288.SH', '农业银行'),
    ('601318.SH', '中国平安'),
    ('601319.SH', '中国人保'),
    ('601336.SH', '新华保险'),
    ('601398.SH', '工商银行'),
    ('601601.SH', '中国太保'),
    ('601628.SH', '中国人寿'),
    ('601633.SH', '长城汽车'),
    ('601668.SH', '中国建筑'),
    ('601688.SH', '华泰证券'),
    ('601766.SH', '中国中车'),
    ('601857.SH', '中国石油'),
    ('601888.SH', '中国中免'),
    ('601899.SH', '紫金矿业'),
    ('601933.SH', '永辉超市'),
    ('601939.SH', '建设银行'),
    ('601988.SH', '中国银行'),
    ('601989.SH', '中国重工'),
    ('603288.SH', '海天味业'),
    ('603501.SH', '韦尔股份'),
    ('603986.SH', '兆易创新'),
    ('603993.SH', '洛阳钼业'),
]


# ==================== 1. Tushare 数据获取 ====================
def init_tushare():
    """初始化 Tushare API"""
    pro = ts.pro_api(TUSHARE_TOKEN)
    return pro


def get_random_stock():
    """
    从预设股票池中随机选择一只股票
    （避免使用需要高积分的 stock_basic 接口）
    
    返回:
        tuple: (股票代码, 股票名称)
    """
    stock = random.choice(STOCK_POOL)
    
    print(f"随机选中股票: {stock[1]} ({stock[0]})")
    
    return stock[0], stock[1]


def get_stock_data(pro, ts_code, days=252):
    """
    获取股票日线数据
    
    参数:
        pro: Tushare API 对象
        ts_code: 股票代码 (如: 000001.SZ)
        days: 获取多少天的数据，默认252个交易日（约1年）
    
    返回:
        DataFrame: 包含 OHLCV 数据
    """
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days * 1.5))  # 留一些余量
    
    end_str = end_date.strftime('%Y%m%d')
    start_str = start_date.strftime('%Y%m%d')
    
    print(f"正在获取数据: {ts_code}")
    print(f"时间范围: {start_str} 至 {end_str}")
    
    # 获取日线数据
    df = pro.daily(ts_code=ts_code, start_date=start_str, end_date=end_str)
    
    if df is None or len(df) == 0:
        raise ValueError(f"未能获取到股票 {ts_code} 的数据")
    
    # 按日期排序
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')
    
    # 取最近 N 个交易日
    df = df.tail(days).reset_index(drop=True)
    df.set_index('trade_date', inplace=True)
    
    # 重命名列以匹配我们的计算函数
    df.rename(columns={
        'open': 'open',
        'high': 'high', 
        'low': 'low',
        'close': 'close',
        'vol': 'volume'  # Tushare 使用 vol 表示成交量（单位：手）
    }, inplace=True)
    
    print(f"✅ 数据获取成功!")
    print(f"实际时间范围: {df.index[0].date()} 至 {df.index[-1].date()}")
    print(f"数据条数: {len(df)} 个交易日")
    
    return df


# ==================== 2. 技术指标计算函数 ====================
def calculate_range(df):
    """
    极差 (Range): 当日最高价与最低价的差值
    
    公式: Range = High - Low
    """
    df['range'] = df['high'] - df['low']
    df['range_pct'] = (df['range'] / df['close']) * 100  # 极差占收盘价的百分比
    
    range_stats = {
        'mean_range': df['range'].mean(),
        'mean_range_pct': df['range_pct'].mean(),
        'max_range': df['range'].max(),
        'max_range_date': df.loc[df['range'].idxmax()].name.strftime('%Y-%m-%d'),
        'min_range': df['range'].min(),
        'current_range': df['range'].iloc[-1],
        'current_range_pct': df['range_pct'].iloc[-1]
    }
    
    return df['range'], range_stats


def calculate_vwap(df):
    """
    VWAP (Volume Weighted Average Price): 成交量加权平均价格
    
    公式: VWAP = Σ(典型价格 × 成交量) / Σ(成交量)
         典型价格 = (High + Low + Close) / 3
    
    注意: 这里计算的是滚动VWAP（从数据起始点开始累积）
    """
    # 典型价格
    tp = (df['high'] + df['low'] + df['close']) / 3
    
    # 累积 VWAP
    df['vwap_cum'] = (tp * df['volume']).cumsum() / df['volume'].cumsum()
    
    # 20日滚动 VWAP（更常用）
    df['vwap_20'] = (tp * df['volume']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
    
    return df['vwap_cum'], df['vwap_20']


def calculate_returns(df):
    """
    收益率计算
    
    1. 简单收益率: R_t = (P_t - P_{t-1}) / P_{t-1}
    2. 对数收益率: r_t = ln(P_t / P_{t-1})
    """
    # 简单收益率
    df['simple_return'] = df['close'].pct_change()
    
    # 对数收益率
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # 累计收益率
    df['cumulative_return'] = (1 + df['simple_return']).cumprod() - 1
    
    # 收益率统计
    return_stats = {
        'total_return': df['cumulative_return'].iloc[-1],
        'annualized_return': ((1 + df['cumulative_return'].iloc[-1]) ** (252 / len(df))) - 1,
        'daily_return_mean': df['simple_return'].mean(),
        'daily_return_std': df['simple_return'].std(),
        'positive_days': (df['simple_return'] > 0).sum(),
        'negative_days': (df['simple_return'] < 0).sum(),
        'max_daily_gain': df['simple_return'].max(),
        'max_daily_loss': df['simple_return'].min(),
        'max_gain_date': df.loc[df['simple_return'].idxmax()].name.strftime('%Y-%m-%d'),
        'max_loss_date': df.loc[df['simple_return'].idxmin()].name.strftime('%Y-%m-%d')
    }
    
    return df[['simple_return', 'log_return', 'cumulative_return']], return_stats


def calculate_volatility(df, windows=[20, 60]):
    """
    波动率计算
    
    1. 日波动率: 对数收益率的标准差
    2. 年化波动率: 日波动率 × √252
    3. 月度波动率: 日波动率 × √21
    
    参数:
        windows: 计算滚动波动率的窗口期列表，默认[20, 60]日
    """
    if 'log_return' not in df.columns:
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    vol_stats = {}
    
    for window in windows:
        # 日波动率
        df[f'daily_vol_{window}'] = df['log_return'].rolling(window=window).std()
        
        # 年化波动率 (252个交易日)
        df[f'annual_vol_{window}'] = df[f'daily_vol_{window}'] * np.sqrt(252)
        
        # 月度波动率 (21个交易日)
        df[f'monthly_vol_{window}'] = df[f'daily_vol_{window}'] * np.sqrt(21)
        
        # 统计最新值
        vol_stats[f'{window}日'] = {
            'daily_vol': df[f'daily_vol_{window}'].iloc[-1],
            'annual_vol': df[f'annual_vol_{window}'].iloc[-1],
            'monthly_vol': df[f'monthly_vol_{window}'].iloc[-1],
            'avg_annual_vol': df[f'annual_vol_{window}'].mean()
        }
    
    return df, vol_stats


# ==================== 3. 综合计算 ====================
def calculate_all_indicators(df):
    """
    计算所有技术指标
    """
    stats = {}
    
    # 1. 极差
    df['range'], range_stats = calculate_range(df)
    stats['极差'] = range_stats
    
    # 2. VWAP
    df['vwap_cum'], df['vwap_20'] = calculate_vwap(df)
    
    # 3. 收益率
    returns_df, return_stats = calculate_returns(df)
    for col in returns_df.columns:
        df[col] = returns_df[col]
    stats['收益率'] = return_stats
    
    # 4. 波动率
    df, vol_stats = calculate_volatility(df, windows=[20, 60])
    stats['波动率'] = vol_stats
    
    return df, stats


# ==================== 4. 可视化 ====================
def plot_analysis(df, stock_name, stock_code):
    """
    绘制综合分析图表
    """
    fig = plt.figure(figsize=(16, 12))
    
    # 创建子图网格
    gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.2)
    
    # 1. K线图 + 极差 (左上)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1_twin = ax1.twinx()
    
    # 绘制收盘价
    ax1.plot(df.index, df['close'], label='收盘价', color='blue', linewidth=1.5)
    ax1.set_ylabel('价格 (元)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    # 绘制极差柱状图
    colors = ['green' if close > open else 'red' for close, open in zip(df['close'], df['open'])]
    ax1_twin.bar(df.index, df['range'], alpha=0.3, color=colors, width=1, label='极差')
    ax1_twin.set_ylabel('极差 (元)', color='gray')
    ax1_twin.tick_params(axis='y', labelcolor='gray')
    
    ax1.set_title(f'{stock_name} ({stock_code}) - 价格与极差')
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    
    # 2. VWAP 对比 (右上)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(df.index, df['close'], label='收盘价', color='blue', linewidth=1.5)
    ax2.plot(df.index, df['vwap_cum'], label='累积VWAP', color='red', linestyle='--', linewidth=1)
    ax2.plot(df.index, df['vwap_20'], label='20日VWAP', color='green', linestyle='-.', linewidth=1)
    ax2.set_title('价格与VWAP对比')
    ax2.legend()
    ax2.set_ylabel('价格 (元)')
    
    # 3. 收益率分布 (左中)
    ax3 = fig.add_subplot(gs[1, 0])
    returns_clean = df['simple_return'].dropna() * 100
    ax3.hist(returns_clean, bins=30, alpha=0.7, edgecolor='black', color='steelblue')
    ax3.axvline(returns_clean.mean(), color='red', linestyle='--', 
                label=f'均值: {returns_clean.mean():.2f}%')
    ax3.axvline(returns_clean.median(), color='green', linestyle='--', 
                label=f'中位数: {returns_clean.median():.2f}%')
    ax3.set_title('日收益率分布')
    ax3.set_xlabel('日收益率 (%)')
    ax3.set_ylabel('频次')
    ax3.legend()
    
    # 4. 累计收益 (右中)
    ax4 = fig.add_subplot(gs[1, 1])
    cumulative_pct = df['cumulative_return'] * 100
    ax4.fill_between(df.index, 0, cumulative_pct, alpha=0.3, 
                     color='green' if cumulative_pct.iloc[-1] > 0 else 'red')
    ax4.plot(df.index, cumulative_pct, color='darkgreen' if cumulative_pct.iloc[-1] > 0 else 'darkred', 
             linewidth=1.5)
    ax4.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax4.set_title('累计收益率走势')
    ax4.set_ylabel('累计收益率 (%)')
    
    # 添加起始和结束收益标注
    ax4.annotate(f'{cumulative_pct.iloc[-1]:.2f}%', 
                 xy=(df.index[-1], cumulative_pct.iloc[-1]),
                 xytext=(10, 0), textcoords='offset points',
                 fontsize=10, fontweight='bold')
    
    # 5. 波动率走势 (左下)
    ax5 = fig.add_subplot(gs[2, :])
    ax5.plot(df.index, df['annual_vol_20'] * 100, label='20日年化波动率', color='purple', linewidth=1)
    ax5.plot(df.index, df['annual_vol_60'] * 100, label='60日年化波动率', color='orange', linewidth=1)
    ax5.axhline(20, color='gray', linestyle='--', alpha=0.5, label='20%参考线')
    ax5.axhline(30, color='red', linestyle='--', alpha=0.5, label='30%参考线')
    ax5.fill_between(df.index, 0, df['annual_vol_20'] * 100, alpha=0.1, color='purple')
    ax5.set_title('年化波动率走势')
    ax5.set_ylabel('年化波动率 (%)')
    ax5.legend()
    
    # 6. 成交量与价格 (右下合并到一行)
    ax6 = fig.add_subplot(gs[3, :])
    ax6_twin = ax6.twinx()
    
    # 成交量柱状图
    volume_colors = ['red' if close < open else 'green' 
                     for close, open in zip(df['close'], df['open'])]
    ax6.bar(df.index, df['volume'] / 10000, alpha=0.5, color=volume_colors, width=1)
    ax6.set_ylabel('成交量 (万手)', color='gray')
    ax6.tick_params(axis='y', labelcolor='gray')
    
    # 收盘价
    ax6_twin.plot(df.index, df['close'], color='blue', linewidth=1.5, label='收盘价')
    ax6_twin.set_ylabel('价格 (元)', color='blue')
    ax6_twin.tick_params(axis='y', labelcolor='blue')
    
    ax6.set_title('成交量与价格')
    ax6.set_xlabel('日期')
    
    plt.savefig(f'week_1/{stock_code.replace(".", "_")}_技术指标分析.png', dpi=150, bbox_inches='tight')
    print(f"\n📊 图表已保存: week_1/{stock_code.replace('.', '_')}_技术指标分析.png")
    plt.show()


# ==================== 5. 主程序 ====================
def main():
    print("=" * 70)
    print("Tushare 真实股票数据 - 技术指标计算")
    print("=" * 70)
    
    try:
        # 初始化 Tushare
        print("\n【1/5】初始化 Tushare API...")
        pro = init_tushare()
        print("✅ API 连接成功")
        
        # 随机选择股票（从预设股票池）
        print("\n【2/5】随机选择股票...")
        stock_code, stock_name = get_random_stock()
        
        # 获取数据
        print("\n【3/5】获取股票日线数据...")
        df = get_stock_data(pro, stock_code, days=252)
        
        print("\n原始数据预览:")
        print(df.tail())
        
        # 计算指标
        print("\n【4/5】计算技术指标...")
        df, stats = calculate_all_indicators(df)
        
        # 输出统计结果
        print("\n" + "=" * 70)
        print("【5/5】计算结果统计")
        print("=" * 70)
        
        # 极差统计
        print("\n📊 极差 (Range) 统计:")
        print(f"  • 平均极差: {stats['极差']['mean_range']:.2f} 元 ({stats['极差']['mean_range_pct']:.2f}%)")
        print(f"  • 最大极差: {stats['极差']['max_range']:.2f} 元 (日期: {stats['极差']['max_range_date']})")
        print(f"  • 最新极差: {stats['极差']['current_range']:.2f} 元 ({stats['极差']['current_range_pct']:.2f}%)")
        
        # 收益率统计
        print("\n📈 收益率统计:")
        print(f"  • 统计期间总收益: {stats['收益率']['total_return']*100:.2f}%")
        print(f"  • 年化收益率: {stats['收益率']['annualized_return']*100:.2f}%")
        print(f"  • 上涨天数: {stats['收益率']['positive_days']} 天")
        print(f"  • 下跌天数: {stats['收益率']['negative_days']} 天")
        print(f"  • 最大单日涨幅: {stats['收益率']['max_daily_gain']*100:.2f}% ({stats['收益率']['max_gain_date']})")
        print(f"  • 最大单日跌幅: {stats['收益率']['max_daily_loss']*100:.2f}% ({stats['收益率']['max_loss_date']})")
        
        # 波动率统计
        print("\n📉 波动率统计:")
        for period, vol_data in stats['波动率'].items():
            print(f"\n  【{period}】")
            print(f"    • 当前年化波动率: {vol_data['annual_vol']*100:.2f}%")
            print(f"    • 平均年化波动率: {vol_data['avg_annual_vol']*100:.2f}%")
            print(f"    • 当前月度波动率: {vol_data['monthly_vol']*100:.2f}%")
        
        # 最新数据
        latest = df.iloc[-1]
        print("\n" + "=" * 70)
        print(f"最新数据 ({df.index[-1].strftime('%Y-%m-%d')}):")
        print("=" * 70)
        print(f"  开盘价: {latest['open']:.2f}")
        print(f"  最高价: {latest['high']:.2f}")
        print(f"  最低价: {latest['low']:.2f}")
        print(f"  收盘价: {latest['close']:.2f}")
        print(f"  成交量: {latest['volume']/10000:.0f} 万手")
        print(f"  极差: {latest['range']:.2f} ({latest['range_pct']:.2f}%)")
        print(f"  20日VWAP: {latest['vwap_20']:.2f}")
        print(f"  20日年化波动率: {latest['annual_vol_20']*100:.2f}%")
        
        # 可视化
        print("\n" + "=" * 70)
        print("生成可视化图表...")
        print("=" * 70)
        plot_analysis(df, stock_name, stock_code)
        
        print("\n✅ 分析完成！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
