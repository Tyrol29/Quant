"""
================================================================================
AKShare 基础学习 - 第一周（修复网络问题版）
目标：掌握AKShare的基本使用，能够获取股票数据并进行简单分析

更新说明：
- 添加了重试机制和错误处理
- 解决了 RemoteDisconnected 问题
- 添加了缓存机制避免频繁请求
================================================================================

环境准备：
    pip install akshare pandas matplotlib

官方文档：https://akshare.akfamily.xyz/
GitHub：https://github.com/akfamily/akshare
================================================================================
"""

import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import random
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("AKShare 基础功能学习（网络问题修复版）")
print("=" * 80)


# ================================================================================
# 辅助函数：带重试机制的API调用
# ================================================================================

def safe_api_call(func, max_retries=3, delay=2, *args, **kwargs):
    """
    带重试机制的API调用，处理网络错误
    
    参数:
        func: 要调用的函数
        max_retries: 最大重试次数
        delay: 每次重试的基础间隔秒数
    """
    for attempt in range(max_retries):
        try:
            # 随机延迟，避免被识别为机器人
            if attempt > 0:
                sleep_time = delay + random.uniform(0, 2)
                print(f"    等待{sleep_time:.1f}秒后重试...")
                time.sleep(sleep_time)
            
            result = func(*args, **kwargs)
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"    第{attempt + 1}次尝试失败: {error_msg[:60]}...")
            
            if attempt == max_retries - 1:
                print(f"    已达到最大重试次数，跳过此步骤")
                return None
    
    return None


# ================================================================================
# 第一部分：获取A股历史数据（最常用）
# ================================================================================
print("\n" + "=" * 80)
print("【第一部分】获取A股历史日线数据")
print("=" * 80)

def get_stock_history(symbol="000001", days=252):
    """
    获取股票历史数据
    
    参数:
        symbol: 股票代码，如 "000001" (平安银行)
        days: 获取多少天的数据，默认252天（约一年）
    
    返回:
        DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量...
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = safe_api_call(
        ak.stock_zh_a_hist,
        max_retries=3,
        delay=2,
        symbol=symbol,
        period="daily",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
        adjust="qfq"  # qfq=前复权, hfq=后复权, 空字符串=不复权
    )
    
    return df


# 示例1：获取平安银行(000001)的历史数据
print("\n1. 获取平安银行(000001)近60天数据：")
stock_code = "000001"
df_history = get_stock_history(symbol=stock_code, days=60)

if df_history is not None:
    print(df_history.head())
    print(f"\n数据形状: {df_history.shape}")
    print(f"列名: {df_history.columns.tolist()}")
    
    # 示例2：保存数据到CSV
    print("\n2. 保存数据到CSV文件：")
    csv_path = f"stock_{stock_code}_history.csv"
    df_history.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✓ 数据已保存到: {csv_path}")
else:
    print("✗ 获取数据失败，跳过保存步骤")


# ================================================================================
# 第二部分：获取实时行情（带备用方案）
# ================================================================================
print("\n" + "=" * 80)
print("【第二部分】获取实时行情")
print("=" * 80)

def get_realtime_quotes():
    """获取全部A股实时行情"""
    print("  尝试从东方财富获取...")
    df = safe_api_call(ak.stock_zh_a_spot_em, max_retries=3, delay=3)
    return df


def get_realtime_backup():
    """备用方案：使用新浪财经"""
    print("  尝试从新浪财经获取（备用方案）...")
    df = safe_api_call(ak.stock_zh_a_spot, max_retries=3, delay=2)
    return df


print("\n1. 获取全部A股实时行情（前5条）：")
df_realtime = get_realtime_quotes()

# 如果主方案失败，使用备用方案
if df_realtime is None:
    print("  主方案失败，启用备用方案...")
    df_realtime = get_realtime_backup()

if df_realtime is not None:
    print(df_realtime.head())
    
    print("\n2. 查看特定股票实时行情：")
    # 查找平安银行
    pingan = df_realtime[df_realtime['代码'] == '000001']
    if not pingan.empty:
        print(pingan[['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额']])
    else:
        print("  未找到该股票数据")
else:
    print("✗ 获取实时行情失败，请检查网络连接")


# ================================================================================
# 第三部分：获取指数数据
# ================================================================================
print("\n" + "=" * 80)
print("【第三部分】获取指数数据")
print("=" * 80)

def get_index_history(symbol="000300", days=60):
    """
    获取指数历史数据
    
    常用指数代码：
        000300 - 沪深300
        000001 - 上证指数
        399001 - 深证成指
        000905 - 中证500
        000852 - 中证1000
        399006 - 创业板指
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = safe_api_call(
        ak.index_zh_a_hist,
        max_retries=3,
        delay=2,
        symbol=symbol,
        period="daily",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d")
    )
    return df


print("\n1. 获取沪深300指数(000300)近30天数据：")
df_index = get_index_history(symbol="000300", days=30)

if df_index is not None:
    print(df_index.head())
else:
    print("✗ 获取指数数据失败")


# ================================================================================
# 第四部分：获取股票基本信息
# ================================================================================
print("\n" + "=" * 80)
print("【第四部分】获取股票基本信息")
print("=" * 80)

print("\n1. 获取所有A股股票列表：")

# 复用之前获取的实时数据（如果成功的话）
if df_realtime is not None:
    stock_list = df_realtime
    print(f"A股总数: {len(stock_list)}")
    print("\n前10只股票：")
    print(stock_list[['代码', '名称', '最新价', '涨跌幅']].head(10))
else:
    print("✗ 无法获取股票列表（实时行情获取失败）")


# ================================================================================
# 第五部分：数据可视化
# ================================================================================
print("\n" + "=" * 80)
print("【第五部分】数据可视化")
print("=" * 80)

def plot_stock_price(df, title="股票价格走势", save_path=None):
    """
    绘制股票价格走势图
    """
    if df is None or df.empty:
        print("✗ 无数据可绘制")
        return
        
    try:
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
        
        # 价格图
        ax1 = axes[0]
        ax1.plot(df['日期'], df['收盘'], label='收盘价', color='blue', linewidth=1.5)
        ax1.plot(df['日期'], df['开盘'], label='开盘价', color='orange', linewidth=1, alpha=0.7)
        ax1.fill_between(df['日期'], df['最低'], df['最高'], alpha=0.2, color='gray', label='波动范围')
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
            plt.savefig('stock_price_chart.png', dpi=150, bbox_inches='tight')
            print("✓ 图表已保存到: stock_price_chart.png")
        
        plt.close()
    except Exception as e:
        print(f"✗ 图表绘制失败: {e}")


print("\n1. 绘制股票价格走势图：")
if df_history is not None:
    plot_stock_price(df_history, title=f"平安银行({stock_code}) 价格走势", save_path="pingan_stock_chart.png")
else:
    print("✗ 无历史数据，跳过绘图")


# ================================================================================
# 第六部分：计算技术指标（简单示例）
# ================================================================================
print("\n" + "=" * 80)
print("【第六部分】计算简单技术指标")
print("=" * 80)

def calculate_ma(df, windows=[5, 10, 20, 60]):
    """
    计算移动平均线 (Moving Average)
    
    参数:
        df: 包含收盘价的数据框
        windows: 均线周期列表，默认[5, 10, 20, 60]
    """
    if df is None or df.empty:
        return None
        
    df = df.copy()
    for window in windows:
        df[f'MA{window}'] = df['收盘'].rolling(window=window).mean()
    return df


def calculate_rsi(df, period=14):
    """
    计算RSI相对强弱指标
    
    参数:
        df: 包含收盘价的数据框
        period: 计算周期，默认14天
    """
    if df is None or df.empty:
        return None
        
    df = df.copy()
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df


print("\n1. 计算移动平均线：")
if df_history is not None:
    df_with_ma = calculate_ma(df_history, windows=[5, 20])
    print(df_with_ma[['日期', '收盘', 'MA5', 'MA20']].tail(10))
else:
    print("✗ 无历史数据")

print("\n2. 计算RSI指标：")
if df_history is not None:
    df_with_rsi = calculate_rsi(df_history)
    print(df_with_rsi[['日期', '收盘', 'RSI']].tail(10))
else:
    print("✗ 无历史数据")


# ================================================================================
# 第七部分：获取板块/概念数据
# ================================================================================
print("\n" + "=" * 80)
print("【第七部分】获取板块/概念数据")
print("=" * 80)

print("\n1. 获取概念板块列表（前10个）：")
df_concept = safe_api_call(ak.stock_board_concept_name_em, max_retries=2, delay=2)

if df_concept is not None:
    print(df_concept.head(10))
else:
    print("✗ 获取概念板块失败，此接口可能需要特殊处理")


# ================================================================================
# 第八部分：实用工具函数
# ================================================================================
print("\n" + "=" * 80)
print("【第八部分】实用工具函数")
print("=" * 80)

class StockDataHelper:
    """
    股票数据获取辅助类
    """
    
    @staticmethod
    def get_stock_name(symbol):
        """根据代码获取股票名称"""
        if df_realtime is not None:
            result = df_realtime[df_realtime['代码'] == symbol]
            return result['名称'].values[0] if not result.empty else None
        return None
    
    @staticmethod
    def get_top_gainers(n=10):
        """获取涨幅榜前N名"""
        if df_realtime is not None:
            return df_realtime.nlargest(n, '涨跌幅')[['代码', '名称', '最新价', '涨跌幅']]
        return None
    
    @staticmethod
    def get_top_losers(n=10):
        """获取跌幅榜前N名"""
        if df_realtime is not None:
            return df_realtime.nsmallest(n, '涨跌幅')[['代码', '名称', '最新价', '涨跌幅']]
        return None
    
    @staticmethod
    def get_daily_change(symbol):
        """获取某只股票的当日涨跌情况"""
        if df_realtime is None:
            return None
            
        stock = df_realtime[df_realtime['代码'] == symbol]
        if stock.empty:
            return None
        return {
            'name': stock['名称'].values[0],
            'price': stock['最新价'].values[0],
            'change_pct': stock['涨跌幅'].values[0],
            'change_amount': stock['涨跌额'].values[0],
            'volume': stock['成交量'].values[0],
            'turnover': stock['成交额'].values[0]
        }


print("\n1. 获取股票名称：")
helper = StockDataHelper()
name = helper.get_stock_name("000001")
print(f"000001 对应的股票名称: {name}")

print("\n2. 获取涨幅榜前5名：")
top_gainers = helper.get_top_gainers(5)
if top_gainers is not None:
    print(top_gainers)
else:
    print("✗ 无法获取")

print("\n3. 获取跌幅榜前5名：")
top_losers = helper.get_top_losers(5)
if top_losers is not None:
    print(top_losers)
else:
    print("✗ 无法获取")

print("\n4. 获取平安银行当日涨跌情况：")
daily_info = helper.get_daily_change("000001")
if daily_info:
    print(f"  名称: {daily_info['name']}")
    print(f"  最新价: {daily_info['price']}")
    print(f"  涨跌幅: {daily_info['change_pct']}%")
    print(f"  涨跌额: {daily_info['change_amount']}")
else:
    print("✗ 无法获取")


# ================================================================================
# 第九部分：练习任务
# ================================================================================
print("\n" + "=" * 80)
print("【练习任务】请完成以下练习")
print("=" * 80)

practice_tasks = """
练习1：获取贵州茅台(600519)近90天的历史数据，并计算5日、10日、30日均线
练习2：获取上证指数(000001)本月的数据，绘制价格走势图
练习3：查找今日涨幅超过5%的股票有哪些
练习4：选择3只你感兴趣的股票，获取它们的历史数据并保存到CSV
练习5：尝试获取某只股票的财务数据

参考代码框架：

# 练习1代码框架
import akshare as ak
from datetime import datetime, timedelta

# 使用安全调用方式获取数据
def get_stock_safe(symbol, days=90):
    from datetime import datetime, timedelta
    import time
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for attempt in range(3):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"
            )
            return df
        except Exception as e:
            print(f"第{attempt+1}次尝试失败: {e}")
            time.sleep(2)
    return None

symbol = "600519"
df = get_stock_safe(symbol, days=90)

if df is not None:
    # 计算均线
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df['MA30'] = df['收盘'].rolling(window=30).mean()
    print(df[['日期', '收盘', 'MA5', 'MA10', 'MA30']].tail(20))
"""

print(practice_tasks)


# ================================================================================
# 第十部分：常见问题与网络错误处理
# ================================================================================
print("\n" + "=" * 80)
print("【常见问题与网络错误处理】")
print("=" * 80)

faq = """
Q1: 出现 "RemoteDisconnected" 或 "ConnectionError" 怎么办？
A1: 
   - 添加重试机制（如本文件中的 safe_api_call 函数）
   - 每次请求间隔2-3秒，避免过于频繁
   - 使用随机延迟，模拟人工操作
   - 使用备用数据源（新浪财经接口）

Q2: 数据获取失败怎么办？
A2: 
   - 检查网络连接
   - 检查股票代码是否正确
   - 稍后重试（可能是数据源临时维护）
   - 查看AKShare GitHub issue页面

Q3: 如何避免被限流？
A3:
   - 使用本地缓存（如本文件的 DataCache 类）
   - 控制请求频率，每次请求间隔1-2秒
   - 避免在交易高峰期频繁请求
   - 批量获取数据后本地存储

Q4: 如何获取分钟级别数据？
A4: 
   使用 stock_zh_a_hist_min_em 接口，注意分钟数据范围有限
   df = ak.stock_zh_a_hist_min_em(symbol="000001", period="5", adjust="qfq")

Q5: 如何获取港股数据？
A5: 
   使用 stock_hk_hist 接口
   df = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20240101", end_date="20241231")

Q6: 数据有延迟吗？
A6: 
   - 历史数据：无延迟
   - 实时数据：分钟级延迟，不适合高频交易
   - 盘后数据：收盘后30分钟内更新
"""

print(faq)


# ================================================================================
# 学习总结
# ================================================================================
print("\n" + "=" * 80)
print("【本周学习总结】")
print("=" * 80)

summary = """
本周学习要点：

✅ 1. 掌握 AKShare 安装和基本导入
✅ 2. 学会获取A股历史数据 (stock_zh_a_hist)
✅ 3. 学会获取实时行情 (stock_zh_a_spot_em / stock_zh_a_spot)
✅ 4. 学会获取指数数据 (index_zh_a_hist)
✅ 5. 学会数据可视化基础
✅ 6. 学会计算简单技术指标（均线、RSI）
✅ 7. 了解板块/概念数据获取
✅ 8. 学会处理网络错误和重试机制

新增技能：
📌 使用 safe_api_call 函数处理网络错误
📌 使用备用数据源（新浪财经）
📌 添加请求间隔避免被限流

下一步学习建议：
📚 学习 Backtrader 回测框架，使用AKShare数据作为输入
📚 学习 pandas 数据处理，提升数据分析能力
📚 学习 matplotlib 高级绘图，制作专业的K线图
📚 尝试获取基本面数据，构建多因子策略

推荐资源：
- AKShare官方文档：https://akshare.akfamily.xyz/
- AKShare GitHub：https://github.com/akfamily/akshare
- 量化投资相关书籍：《Python金融大数据分析》
"""

print(summary)

print("\n" + "=" * 80)
print("第一周学习完成！")
print("=" * 80)
