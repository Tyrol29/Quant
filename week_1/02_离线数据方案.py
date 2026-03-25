"""
================================================================================
离线数据方案 - 当AKShare网络不稳定时使用
方案A：使用Tushare（更稳定，但有积分限制）
方案B：使用本地模拟数据（练习代码逻辑）
方案C：使用Yahoo Finance（适合美股+A股，稳定）
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import random

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("离线数据方案 - 绕开网络限制")
print("=" * 80)


# ================================================================================
# 方案A：使用 Tushare（推荐）
# ================================================================================
print("\n" + "=" * 80)
print("【方案A】使用 Tushare（推荐，更稳定）")
print("=" * 80)

def use_tushare():
    """
    Tushare 使用说明：
    1. 注册账号：https://tushare.pro/register
    2. 获取Token：个人中心 -> 接口TOKEN
    3. 免费版有积分限制，但学习够用
    """
    try:
        import tushare as ts
        
        # 初始化（需要你注册后填入自己的token）
        # ts.set_token('你的token')
        # pro = ts.pro_api()
        
        print("""
Tushare 使用步骤：
1. 访问 https://tushare.pro/register 注册账号
2. 登录后获取你的Token
3. 修改下方代码中的 token

示例代码：
    import tushare as ts
    ts.set_token('你的token')
    pro = ts.pro_api()
    
    # 获取日线数据
    df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20241231')
    
    # 获取实时行情
    df = pro.query('daily_basic', ts_code='', trade_date='20240325')
        """)
        
        return True
    except ImportError:
        print("Tushare 未安装，请运行: pip install tushare")
        return False


use_tushare()


# ================================================================================
# 方案B：使用 Yahoo Finance（免费且稳定）
# ================================================================================
print("\n" + "=" * 80)
print("【方案B】使用 Yahoo Finance（免费且稳定，支持A股）")
print("=" * 80)

def use_yfinance():
    """
    Yahoo Finance 方案：
    - 优点：免费、稳定、全球股票数据
    - 缺点：A股数据有15分钟延迟
    - 安装：pip install yfinance
    """
    try:
        import yfinance as yf
        
        print("✓ yfinance 已安装，尝试获取数据...")
        
        # A股代码格式：股票代码.SS（上海）或 .SZ（深圳）
        # 例如：000001.SZ（平安银行）、600519.SS（茅台）
        ticker = yf.Ticker("000001.SZ")  # 平安银行
        
        # 获取历史数据
        df = ticker.history(period="3mo")  # 3个月数据
        
        print(f"✓ 成功获取数据，共 {len(df)} 条")
        print(df.head())
        
        return df
        
    except ImportError:
        print("yfinance 未安装，请运行: pip install yfinance")
        return None
    except Exception as e:
        print(f"✗ 获取数据失败: {e}")
        return None


# 运行Yahoo Finance方案
df_yahoo = use_yfinance()

if df_yahoo is not None:
    print("\n Yahoo Finance 数据列名：")
    print(df_yahoo.columns.tolist())


# ================================================================================
# 方案C：本地模拟数据（完全离线，练习代码逻辑）
# ================================================================================
print("\n" + "=" * 80)
print("【方案C】本地模拟数据（完全离线，练习代码逻辑）")
print("=" * 80)

def generate_mock_stock_data(symbol="000001", days=60, trend="random"):
    """
    生成模拟股票数据
    
    参数:
        symbol: 股票代码
        days: 生成多少天的数据
        trend: 'up'(上涨), 'down'(下跌), 'random'(随机)
    
    返回:
        DataFrame 格式与AKShare一致
    """
    # 生成日期序列（排除周末）
    dates = []
    current = datetime.now() - timedelta(days=days*2)  # 多生成一些天数，后续过滤
    
    while len(dates) < days:
        if current.weekday() < 5:  # 周一到周五
            dates.append(current)
        current += timedelta(days=1)
    
    # 生成价格数据
    np.random.seed(42)  # 固定随机种子，保证可重复
    
    initial_price = 10.0  # 初始价格
    prices = [initial_price]
    
    for i in range(1, len(dates)):
        if trend == "up":
            change = np.random.normal(0.001, 0.02)  # 轻微上涨趋势
        elif trend == "down":
            change = np.random.normal(-0.001, 0.02)  # 轻微下跌趋势
        else:  # random
            change = np.random.normal(0, 0.02)  # 纯随机
        
        new_price = prices[-1] * (1 + change)
        new_price = max(new_price, 1.0)  # 价格不低于1元
        prices.append(new_price)
    
    # 生成OHLC数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 基于收盘价生成开高低
        volatility = 0.01  # 日内波动率
        open_price = close * (1 + np.random.normal(0, volatility))
        high_price = max(open_price, close) * (1 + abs(np.random.normal(0, volatility)))
        low_price = min(open_price, close) * (1 - abs(np.random.normal(0, volatility)))
        
        # 成交量（随机）
        volume = int(np.random.uniform(1000000, 10000000))
        
        # 涨跌幅计算
        if i > 0:
            change_pct = (close - prices[i-1]) / prices[i-1] * 100
        else:
            change_pct = 0
        
        data.append({
            '日期': date.strftime('%Y-%m-%d'),
            '开盘': round(open_price, 2),
            '收盘': round(close, 2),
            '最高': round(high_price, 2),
            '最低': round(low_price, 2),
            '成交量': volume,
            '成交额': round(volume * close, 2),
            '振幅': round((high_price - low_price) / low_price * 100, 2),
            '涨跌幅': round(change_pct, 2),
            '涨跌额': round(close - open_price, 2),
            '换手率': round(np.random.uniform(0.5, 3.0), 2)
        })
    
    df = pd.DataFrame(data)
    
    # 添加股票代码列
    df['股票代码'] = symbol
    
    print(f"✓ 生成 {symbol} 模拟数据 {len(df)} 条")
    return df


# 生成模拟数据
print("\n1. 生成上涨趋势的模拟数据（平安银行）：")
df_mock_up = generate_mock_stock_data("000001", days=60, trend="up")
print(df_mock_up.head())

print("\n2. 生成随机趋势的模拟数据（茅台）：")
df_mock_random = generate_mock_stock_data("600519", days=60, trend="random")
print(df_mock_random.head())


# 保存模拟数据到CSV
df_mock_up.to_csv("mock_stock_000001.csv", index=False, encoding='utf-8-sig')
print("\n✓ 模拟数据已保存到: mock_stock_000001.csv")


# ================================================================================
# 方案D：使用已保存的本地数据
# ================================================================================
print("\n" + "=" * 80)
print("【方案D】使用已保存的本地数据（如果之前成功获取过）")
print("=" * 80)

def load_local_data(filepath):
    """加载本地CSV数据"""
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        print(f"✓ 成功加载本地数据: {filepath}，共 {len(df)} 条")
        return df
    except FileNotFoundError:
        print(f"✗ 文件不存在: {filepath}")
        return None
    except Exception as e:
        print(f"✗ 加载失败: {e}")
        return None


# 尝试加载之前保存的数据
import os

# 检查当前目录下的CSV文件
csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
print(f"\n发现本地CSV文件: {csv_files}")

if csv_files:
    for csv_file in csv_files[:2]:  # 只加载前2个
        df_local = load_local_data(csv_file)
        if df_local is not None:
            print(f"\n{csv_file} 的前5行:")
            print(df_local.head())


# ================================================================================
# 方案E：使用聚宽/果仁网数据（在线平台）
# ================================================================================
print("\n" + "=" * 80)
print("【方案E】使用在线量化平台（推荐长期方案）")
print("=" * 80)

def recommend_platforms():
    """推荐在线量化平台"""
    platforms = """
推荐平台（数据稳定，适合学习）：

1. 聚宽 JoinQuant (https://www.joinquant.com/)
   - 优点：免费、数据完整、文档丰富
   - 数据：A股2005年至今完整数据
   - 费用：免费版足够学习
   - 建议：注册后使用网页版研究环境

2. 果仁网 (https://guorn.com/)
   - 优点：操作简单、无需编程基础
   - 数据：A股基本面+量价数据
   - 费用：免费版可用

3. 优矿 Uqer (https://uqer.io/)
   - 优点：通联数据支持、数据质量高
   - 数据：多维度金融数据
   - 费用：免费版有额度限制

4. RiceQuant 米筐 (https://www.ricequant.com/)
   - 优点：数据全面、支持多种资产
   - 数据：A股、期货、期权等
   - 费用：免费版可用

建议操作：
1. 立即注册聚宽账号（免费）
2. 使用网页版研究环境练习
3. 数据由平台提供，无需担心网络问题
"""
    print(platforms)


recommend_platforms()


# ================================================================================
# 使用模拟数据进行技术指标计算（练习用）
# ================================================================================
print("\n" + "=" * 80)
print("【使用模拟数据练习技术指标】")
print("=" * 80)

def calculate_ma(df, windows=[5, 10, 20, 60]):
    """计算移动平均线"""
    df = df.copy()
    for window in windows:
        df[f'MA{window}'] = df['收盘'].rolling(window=window).mean()
    return df


def calculate_rsi(df, period=14):
    """计算RSI"""
    df = df.copy()
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df


# 使用模拟数据计算指标
print("\n1. 计算移动平均线：")
df_with_ma = calculate_ma(df_mock_up, windows=[5, 20])
print(df_with_ma[['日期', '收盘', 'MA5', 'MA20']].tail(10))

print("\n2. 计算RSI指标：")
df_with_rsi = calculate_rsi(df_mock_up)
print(df_with_rsi[['日期', '收盘', 'RSI']].tail(10))


# ================================================================================
# 数据可视化（使用模拟数据）
# ================================================================================
print("\n" + "=" * 80)
print("【数据可视化（使用模拟数据）】")
print("=" * 80)

def plot_stock_price(df, title="股票价格走势", save_path=None):
    """绘制股票价格走势图"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # 日期转datetime
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 价格图
    ax1 = axes[0]
    ax1.plot(df['日期'], df['收盘'], label='收盘价', color='blue', linewidth=1.5)
    if 'MA5' in df.columns:
        ax1.plot(df['日期'], df['MA5'], label='MA5', color='orange', linewidth=1)
    if 'MA20' in df.columns:
        ax1.plot(df['日期'], df['MA20'], label='MA20', color='red', linewidth=1)
    ax1.set_title(title, fontsize=14)
    ax1.set_ylabel('价格 (元)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 成交量图
    ax2 = axes[1]
    colors = ['red' if close >= open else 'green' for close, open in zip(df['收盘'], df['开盘'])]
    ax2.bar(df['日期'], df['成交量'], color=colors, alpha=0.7)
    ax2.set_ylabel('成交量', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✓ 图表已保存到: {save_path}")
    else:
        plt.savefig('mock_stock_chart.png', dpi=150, bbox_inches='tight')
        print("✓ 图表已保存到: mock_stock_chart.png")
    
    plt.close()


# 绘制模拟数据图表
plot_stock_price(df_with_ma, title="模拟股票走势（带均线）", save_path="mock_stock_chart.png")


# ================================================================================
# 总结与建议
# ================================================================================
print("\n" + "=" * 80)
print("【总结与建议】")
print("=" * 80)

summary = """
当前网络问题总结：

问题：AKShare的东方财富接口对IP限流
原因：
- 短时间内多次请求
- 当前网络环境被标记
- 东方财富服务端限流

即时解决方案（按推荐顺序）：

1. 【推荐】使用模拟数据练习（本文件已实现）
   - 优点：完全离线，可重复运行
   - 适用：学习Python代码逻辑、练习技术指标计算
   - 数据质量：虽为模拟，但格式与真实数据一致

2. 【次选】使用 Yahoo Finance（yfinance）
   - 安装：pip install yfinance
   - A股代码格式：000001.SZ（深圳）、600519.SS（上海）
   - 稳定性：较好，但有15分钟延迟

3. 【长期】注册聚宽等在线平台
   - 数据稳定，无需担心网络问题
   - 有完善的研究环境和回测功能

4. 【备选】使用 Tushare
   - 需要注册获取Token
   - 免费版有积分限制，但学习够用

本周学习计划调整：

原 plan A：使用AKShare获取实时数据
新 plan B：使用模拟数据 + 本地文件学习

学习效果对比：
✓ Python数据处理技能 - 相同
✓ 技术指标计算方法 - 相同
✓ 数据可视化技能 - 相同
✓ 策略回测逻辑 - 相同
✗ 真实市场数据体验 - 略差（但后续可补）

建议：
1. 先用模拟数据完成本周学习
2. 明天或后天再尝试AKShare（限流通常24小时恢复）
3. 同时注册聚宽账号，作为备用方案
4. 学习完成后，再将代码应用到真实数据
"""

print(summary)

print("\n" + "=" * 80)
print("方案文件使用说明：")
print("=" * 80)
print("""
1. 运行本文件，生成模拟数据并练习
2. 对比模拟数据和真实数据的差异
3. 完成技术指标计算练习
4. 保存图表和CSV文件

明天尝试：
- 再次运行AKShare代码（限流可能已恢复）
- 或注册聚宽账号，开始在线学习
""")
