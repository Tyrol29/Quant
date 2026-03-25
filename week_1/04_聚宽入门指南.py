"""
================================================================================
聚宽（JoinQuant）入门指南
从AKShare迁移到聚宽平台的完整教程
================================================================================

聚宽优势：
- 数据稳定，无需担心网络问题
- 自带回测引擎，无需安装Backtrader
- 免费版足够学习使用
- 有完善的研究环境和文档

官方文档：https://www.joinquant.com/help/api/help
================================================================================
"""

print("=" * 80)
print("聚宽（JoinQuant）入门指南")
print("=" * 80)


# ================================================================================
# 第一部分：聚宽与AKShare的主要区别
# ================================================================================

print("\n" + "=" * 80)
print("【第一部分】聚宽 vs AKShare 对比")
print("=" * 80)

comparison = """
┌─────────────────┬──────────────────┬──────────────────┐
│     项目        │     AKShare      │      聚宽        │
├─────────────────┼──────────────────┼──────────────────┤
│ 数据获取方式    │ 本地Python调用   │ 在线平台API      │
│ 网络要求        │ 需要联网下载     │ 平台已内置数据   │
│ 回测功能        │ 需安装Backtrader │ 自带回测引擎     │
│ 数据更新        │ 实时/延迟        │ 收盘后更新       │
│ 运行环境        │ 本地Python       │ 网页/本地均可    │
│ 费用            │ 完全免费         │ 免费版足够学习   │
│ 稳定性          │ 可能限流         │ 非常稳定         │
└─────────────────┴──────────────────┴──────────────────┘

关键概念转换：

AKShare                     聚宽
──────────────────────────────────────────────
import akshare as ak    →   # 聚宽不需要导入
ak.stock_zh_a_hist()    →   get_price() 或 attribute_history()
ak.stock_zh_a_spot_em() →   get_current_data()
pandas DataFrame        →   pandas DataFrame（相同）
本地CSV存储             →   平台自动存储
matplotlib绘图          →   平台内置绘图 或 matplotlib
"""

print(comparison)


# ================================================================================
# 第二部分：聚宽核心API速查
# ================================================================================

print("\n" + "=" * 80)
print("【第二部分】聚宽核心API速查")
print("=" * 80)

api_guide = """
═══════════════════════════════════════════════════════════════════════════════
【数据获取类API】
═══════════════════════════════════════════════════════════════════════════════

1. 获取历史数据（最常用）
───────────────────────────────────────────────────────────────────────────────
# 获取单只股票历史数据
df = get_price('000001.XSHE',           # 股票代码（聚宽格式）
               count=100,                # 获取多少条
               frequency='1d',           # 频率：1d=日线, 1m=分钟
               fields=['open', 'high', 'low', 'close', 'volume', 'money'],
               skip_paused=True,         # 跳过停牌
               fq='pre')                 # 复权：pre=前复权, post=后复权

# 获取多只股票的 Panel 数据（用于多因子）
df = get_price(['000001.XSHE', '600000.XSHG'],
               start_date='2024-01-01',
               end_date='2024-12-31',
               frequency='1d',
               panel=False)               # panel=False返回DataFrame


2. 获取实时行情
df = get_current_data()                   # 获取全部股票实时数据
price = get_current_data()['000001.XSHE'].day_open  # 获取开盘价


3. 获取财务数据
df = get_fundamentals(query(indicator),  # 财务指标
                      date='2024-03-25')  # 指定日期

# 获取特定指标
df = get_fundamentals(query(
    valuation.code,                       # 股票代码
    valuation.pe_ratio,                   # 市盈率
    valuation.pb_ratio,                   # 市净率
    indicator.roe                         # 净资产收益率
).filter(
    valuation.code == '000001.XSHE'
))


4. 获取股票列表
stocks = get_all_securities(types=['stock'],          # 获取所有股票
                           date='2024-01-01')        # 指定日期

index_stocks = get_index_stocks('000300.XSHG')       # 获取沪深300成分股


═══════════════════════════════════════════════════════════════════════════════
【交易相关API】
═══════════════════════════════════════════════════════════════════════════════

1. 下单
order('000001.XSHE', 100)                 # 买入100股
order_target('000001.XSHE', 1000)         # 调整到1000股
order_value('000001.XSHE', 10000)         # 买入10000元的股票
order_target_value('000001.XSHE', 50000)  # 调整到持有50000元市值


2. 获取持仓
context.portfolio.positions               # 当前所有持仓
context.portfolio.positions_value         # 持仓总市值
context.portfolio.available_cash          # 可用现金
context.portfolio.total_value             # 总资产


═══════════════════════════════════════════════════════════════════════════════
【定时运行API】
═══════════════════════════════════════════════════════════════════════════════

# 设置定时运行（在init函数中）
run_daily(trade, time='9:30')             # 每天9:30运行
trun_daily(trade, time='open')            # 开盘时运行
trun_daily(trade, time='close')           # 收盘时运行
trun_daily(trade, time='before_open')     # 开盘前运行

# 其他频率
run_weekly(trade, weekday=1, time='open') # 每周一开盘运行
run_monthly(trade, monthday=1, time='open') # 每月1号开盘运行


═══════════════════════════════════════════════════════════════════════════════
【代码转换示例】
═══════════════════════════════════════════════════════════════════════════════

【AKShare代码】
import akshare as ak
df = ak.stock_zh_a_hist(symbol="000001", 
                        period="daily",
                        start_date="20240101",
                        end_date="20241231",
                        adjust="qfq")

【聚宽代码】
df = get_price('000001.XSHE',
               start_date='2024-01-01',
               end_date='2024-12-31',
               frequency='1d',
               fq='pre',
               panel=False)

注意代码格式区别：
- AKShare: 000001（6位数字）
- 聚宽: 000001.XSHE（深圳）或 600000.XSHG（上海）
"""

print(api_guide)


# ================================================================================
# 第三部分：聚宽策略模板
# ================================================================================

print("\n" + "=" * 80)
print("【第三部分】聚宽策略模板（可直接复制到平台使用）")
print("=" * 80)

strategy_template = '''
# 聚宽策略模板 - 双均线策略
# 复制到聚宽网站：https://www.joinquant.com/
# 点击"我的策略" -> "新建策略" -> 粘贴代码

# ========== 初始化函数 ==========
def initialize(context):
    """
    初始化函数，只运行一次
    """
    # 设置基准
    set_benchmark('000300.XSHG')  # 沪深300
    
    # 设置佣金和印花税
    set_order_cost(OrderCost(
        open_tax=0,                 # 买入印花税
        close_tax=0.001,            # 卖出印花税（千分之一）
        open_commission=0.0003,     # 买入佣金（万分之三）
        close_commission=0.0003,    # 卖出佣金
        close_today_commission=0,   # 平今佣金
        min_commission=5            # 最低佣金
    ), type='stock')
    
    # 设置滑点
    set_slippage(FixedSlippage(0.002))  # 固定滑点
    
    # 设置参数
    context.security = '000001.XSHE'     # 平安银行
    context.short_window = 5             # 短期均线
    context.long_window = 20             # 长期均线
    
    # 设置定时运行（每天开盘前运行）
    run_daily(before_market_open, time='before_open')
    # 设置定时运行（每天开盘时运行）
    run_daily(market_open, time='open')
    # 设置定时运行（每天收盘后运行）
    run_daily(after_market_close, time='after_close')


def before_market_open(context):
    """
    开盘前运行：获取数据、计算信号
    """
    # 获取历史数据
    hist = attribute_history(context.security, 
                            context.long_window + 10, 
                            '1d', 
                            ['close'], 
                            skip_paused=True)
    
    # 计算均线
    short_ma = hist['close'][-context.short_window:].mean()
    long_ma = hist['close'][-context.long_window:].mean()
    
    # 记录到上下文
    context.short_ma = short_ma
    context.long_ma = long_ma
    
    log.info(f"开盘前计算：MA{context.short_window}={short_ma:.2f}, MA{context.long_window}={long_ma:.2f}")


def market_open(context):
    """
    开盘时运行：执行交易
    """
    security = context.security
    
    # 获取当前价格
    current_data = get_current_data()
    if current_data[security].paused:
        log.info("股票停牌，跳过")
        return
    
    current_price = current_data[security].day_open
    
    # 获取当前持仓
    holding = context.portfolio.positions.get(security, None)
    
    # 交易逻辑
    if context.short_ma > context.long_ma:
        # 金叉，买入
        if holding is None or holding.total_amount == 0:
            # 计算可买入数量（全仓）
            cash = context.portfolio.available_cash
            amount = int(cash / current_price / 100) * 100  # 100股整数倍
            
            if amount > 0:
                order(security, amount)
                log.info(f"买入 {security} {amount}股 @ {current_price:.2f}")
    else:
        # 死叉，卖出
        if holding is not None and holding.total_amount > 0:
            order_target(security, 0)
            log.info(f"卖出 {security} {holding.total_amount}股 @ {current_price:.2f}")


def after_market_close(context):
    """
    收盘后运行：记录日志
    """
    # 记录账户信息
    log.info('一天结束')
    log.info('############################')
    log.info(f"总资产: {context.portfolio.total_value:.2f}")
    log.info(f"持仓市值: {context.portfolio.positions_value:.2f}")
    log.info(f"可用现金: {context.portfolio.available_cash:.2f}")
    log.info('############################')


# ========== 策略说明 ==========
"""
策略名称：双均线策略
策略逻辑：
1. 计算5日均线和20日均线
2. 当5日均线上穿20日均线（金叉）时买入
3. 当5日均线下穿20日均线（死叉）时卖出
4. 回测周期：2024-01-01 到 2024-12-31
5. 初始资金：100000元
"""
'''

print(strategy_template)


# ================================================================================
# 第四部分：研究环境使用（IPython Notebook）
# ================================================================================

print("\n" + "=" * 80)
print("【第四部分】聚宽研究环境使用")
print("=" * 80)

research_guide = """
═══════════════════════════════════════════════════════════════════════════════
【什么是研究环境？】
═══════════════════════════════════════════════════════════════════════════════

聚宽提供类似Jupyter Notebook的研究环境，可以：
- 交互式探索数据
- 测试策略逻辑
- 可视化分析
- 调试代码

═══════════════════════════════════════════════════════════════════════════════
【使用步骤】
═══════════════════════════════════════════════════════════════════════════════

1. 进入研究环境
   - 登录聚宽：https://www.joinquant.com/
   - 点击顶部菜单 "研究"
   - 点击 "新建研究"

2. 常用代码示例
───────────────────────────────────────────────────────────────────────────────

# 获取一只股票的历史数据
import pandas as pd

df = get_price('000001.XSHE', 
               start_date='2024-01-01', 
               end_date='2024-12-31',
               frequency='1d',
               panel=False)
print(df.head())

# 绘图
import matplotlib.pyplot as plt
df['close'].plot(figsize=(12, 6))
plt.title('平安银行收盘价')
plt.show()

# 计算均线
df['MA5'] = df['close'].rolling(5).mean()
df['MA20'] = df['close'].rolling(20).mean()

# 绘制均线图
df[['close', 'MA5', 'MA20']].plot(figsize=(12, 6))
plt.title('平安银行价格与均线')
plt.show()

# 获取多只股票数据
stocks = ['000001.XSHE', '600000.XSHG', '600519.XSHG']
df = get_price(stocks, 
               start_date='2024-01-01', 
               end_date='2024-12-31',
               frequency='1d',
               panel=False)
print(df.head())

# 获取股票基本信息
stocks = get_all_securities(types=['stock'], date='2024-01-01')
print(stocks.head())

# 获取财务数据
from jqdata import *

df = get_fundamentals(query(
    valuation.code,
    valuation.pe_ratio,
    valuation.pb_ratio,
    indicator.roe
).filter(
    valuation.code.in_(['000001.XSHE', '600000.XSHG'])
), date='2024-03-25')

print(df)

═══════════════════════════════════════════════════════════════════════════════
【代码转换：AKShare → 聚宽研究环境】
═══════════════════════════════════════════════════════════════════════════════

【原AKShare代码】
import akshare as ak
import pandas as pd

# 获取数据
df = ak.stock_zh_a_hist(symbol="000001", 
                        period="daily",
                        start_date="20240101",
                        end_date="20241231",
                        adjust="qfq")

# 计算均线
df['MA5'] = df['收盘'].rolling(5).mean()
df['MA20'] = df['收盘'].rolling(20).mean()

# 绘图
import matplotlib.pyplot as plt
plt.plot(df['日期'], df['收盘'])
plt.show()

【聚宽研究环境代码】
# 获取数据（注意代码格式不同）
df = get_price('000001.XSHE',               # 聚宽格式：代码.交易所
               start_date='2024-01-01',     # 日期格式不同
               end_date='2024-12-31',
               frequency='1d',
               fq='pre',                    # pre=前复权
               panel=False)

# 计算均线（列名不同）
df['MA5'] = df['close'].rolling(5).mean()   # close 而不是 收盘
df['MA20'] = df['close'].rolling(20).mean()

# 绘图（相同）
import matplotlib.pyplot as plt
df['close'].plot()                          # 聚宽DataFrame可以直接plot
plt.show()

═══════════════════════════════════════════════════════════════════════════════
【关键区别总结】
═══════════════════════════════════════════════════════════════════════════════

1. 股票代码格式
   AKShare: "000001"
   聚宽: "000001.XSHE"（深交所）或 "600000.XSHG"（上交所）

2. 日期格式
   AKShare: "20240101"（YYYYMMDD）
   聚宽: "2024-01-01"（YYYY-MM-DD）

3. 列名
   AKShare: '开盘', '收盘', '最高', '最低', '成交量'
   聚宽: 'open', 'close', 'high', 'low', 'volume'

4. 函数名
   AKShare: stock_zh_a_hist()
   聚宽: get_price() 或 attribute_history()

5. 导入方式
   AKShare: import akshare as ak
   聚宽: 不需要导入，函数直接使用
"""

print(research_guide)


# ================================================================================
# 第五部分：回测设置指南
# ================================================================================

print("\n" + "=" * 80)
print("【第五部分】回测设置指南")
print("=" * 80)

backtest_guide = """
═══════════════════════════════════════════════════════════════════════════════
【创建回测步骤】
═══════════════════════════════════════════════════════════════════════════════

1. 点击 "我的策略" → "新建策略"
2. 选择模板（建议选"股票策略模板"）
3. 粘贴策略代码
4. 点击 "回测" 标签
5. 设置回测参数：

回测参数设置：
───────────────────────────────────────────────────────────────────────────────
时间范围：
  开始日期：2024-01-01
  结束日期：2024-12-31

资金设置：
  初始资金：100000（10万元）
  回测频率：每天
   benchmark：000300.XSHG（沪深300指数）

═══════════════════════════════════════════════════════════════════════════════
【查看回测结果】
═══════════════════════════════════════════════════════════════════════════════

回测完成后可以看到：
1. 收益曲线图（策略收益 vs 基准收益）
2. 回测指标：
   - 年化收益率
   - 最大回撤
   - 夏普比率
   - 胜率
   - 盈亏比
3. 交易记录：每笔买入卖出的详情
4. 持仓记录：每天持仓情况

═══════════════════════════════════════════════════════════════════════════════
【模拟交易】
═══════════════════════════════════════════════════════════════════════════════

回测验证策略有效后，可以开启模拟交易：

1. 点击 "模拟交易" 标签
2. 点击 "开启模拟交易"
3. 策略会在实盘时间自动运行
4. 每天发送交易信号到你的微信/邮件

注意：模拟交易使用实时数据，但只是模拟，不真钱交易
"""

print(backtest_guide)


# ================================================================================
# 第六部分：将你的AKShare代码迁移到聚宽
# ================================================================================

print("\n" + "=" * 80)
print("【第六部分】代码迁移示例")
print("=" * 80)

migration_example = """
【原AKShare代码 - 获取数据并计算均线】

import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

# 获取数据
df = ak.stock_zh_a_hist(symbol="000001", 
                        period="daily",
                        start_date="20240101",
                        end_date="20241231",
                        adjust="qfq")

# 计算指标
df['MA5'] = df['收盘'].rolling(5).mean()
df['MA20'] = df['收盘'].rolling(20).mean()

# 绘图
plt.figure(figsize=(12, 6))
plt.plot(df['日期'], df['收盘'], label='收盘价')
plt.plot(df['日期'], df['MA5'], label='MA5')
plt.plot(df['日期'], df['MA20'], label='MA20')
plt.legend()
plt.show()


【迁移到聚宽研究环境】

# 获取数据（注意代码和日期格式）
df = get_price('000001.XSHE', 
               start_date='2024-01-01', 
               end_date='2024-12-31',
               frequency='1d',
               fq='pre',
               panel=False)

# 计算指标（注意列名是英文）
df['MA5'] = df['close'].rolling(5).mean()
df['MA20'] = df['close'].rolling(20).mean()

# 绘图（相同）
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'], label='收盘价')  # 日期是index
plt.plot(df.index, df['MA5'], label='MA5')
plt.plot(df.index, df['MA20'], label='MA20')
plt.legend()
plt.show()


【迁移到聚宽策略（自动交易）】

def initialize(context):
    set_benchmark('000300.XSHG')
    g.security = '000001.XSHE'  # 全局变量用 g. 开头
    run_daily(trade, time='open')

def trade(context):
    security = g.security
    
    # 获取历史数据
    hist = attribute_history(security, 30, '1d', ['close'], skip_paused=True)
    
    # 计算均线
    ma5 = hist['close'][-5:].mean()
    ma20 = hist['close'][-20:].mean()
    
    # 交易逻辑...
    if ma5 > ma20:
        order_value(security, 10000)  # 买入1万元
    else:
        order_target(security, 0)      # 清仓
"""

print(migration_example)


# ================================================================================
# 第七部分：常见问题
# ================================================================================

print("\n" + "=" * 80)
print("【第七部分】常见问题")
print("=" * 80)

faq = """
Q1: 聚宽股票代码格式是什么？
A1: 
   深交所股票：000001.XSHE（平安银行）
   上交所股票：600000.XSHG（浦发银行）
   创业板：300001.XSHE（特锐德）
   科创板：688001.XSHG（华兴源创）
   北交所：430047.XBSE（诺思兰德）

Q2: 如何查看聚宽支持哪些函数？
A2: 
   - 官方API文档：https://www.joinquant.com/help/api/help
   - 在策略中按 Tab 键有代码提示
   - 在研究环境中使用 help(get_price)

Q3: 聚宽数据有延迟吗？
A3:
   - 历史数据：无延迟，收盘后更新
   - 模拟交易：使用实时数据，但信号可能有分钟级延迟
   - 分钟数据：免费提供，但有访问频率限制

Q4: 免费版和付费版有什么区别？
A4:
   免费版：
   - 回测时间范围：最近2年
   - 模拟交易：1个策略
   - 分钟数据：有限访问
   
   付费版：
   - 更长回测时间
   - 更多模拟交易名额
   - 更高频率数据访问
   
   学习阶段免费版完全够用！

Q5: 如何将策略导出到本地运行？
A5:
   - 聚宽策略只能在平台运行（代码依赖平台API）
   - 但可以导出交易记录和数据
   - 如果想本地运行，需要使用AKShare/QMT等替代

Q6: 聚宽可以实盘交易吗？
A6:
   - 聚宽本身不支持直接实盘
   - 但可以使用 "易盛9.0" 等第三方工具对接
   - 或使用 " ricequant米筐" 的实盘功能（付费）
   - 一般建议先用模拟交易验证策略
"""

print(faq)


# ================================================================================
# 总结与下一步
# ================================================================================

print("\n" + "=" * 80)
print("【总结与下一步】")
print("=" * 80)

summary = """
═══════════════════════════════════════════════════════════════════════════════
【你现在应该做的】
═══════════════════════════════════════════════════════════════════════════════

第1步：熟悉研究环境（今天）
───────────────────────────────────────────────────────────────────────────────
- 登录聚宽：https://www.joinquant.com/
- 点击 "研究" → "新建研究"
- 尝试运行以下代码：

  df = get_price('000001.XSHE', count=100, panel=False)
  print(df.head())
  df['close'].plot()

第2步：创建第一个策略（今天）
───────────────────────────────────────────────────────────────────────────────
- 点击 "我的策略" → "新建策略"
- 复制本文件中的"策略模板"代码
- 点击回测，查看结果

第3步：修改策略参数（明天）
───────────────────────────────────────────────────────────────────────────────
- 修改均线周期（如5日→10日）
- 修改股票代码（如平安银行→茅台600519.XSHG）
- 添加止损逻辑
- 观察回测结果变化

第4步：多因子策略（本周内）
───────────────────────────────────────────────────────────────────────────────
- 学习获取财务数据
- 构建PE、PB、ROE等因子
- 实现多因子选股策略

第5步：开启模拟交易（策略稳定后）
───────────────────────────────────────────────────────────────────────────────
- 回测收益稳定后
- 开启模拟交易观察1-2周
- 确认信号符合预期

═══════════════════════════════════════════════════════════════════════════════
【学习资源】
═══════════════════════════════════════════════════════════════════════════════

- 聚宽学院：https://www.joinquant.com/college
- API文档：https://www.joinquant.com/help/api/help
- 策略广场：https://www.joinquant.com/algorithm（看别人写的策略）
- 社区讨论：https://www.joinquant.com/community

═══════════════════════════════════════════════════════════════════════════════
【与之前AKShare学习的衔接】
═══════════════════════════════════════════════════════════════════════════════

你已经掌握的（不变）：
✓ Python基础语法
✓ Pandas数据处理
✓ Matplotlib可视化
✓ 技术指标计算逻辑（MA、RSI等）
✓ 策略逻辑（金叉买入、死叉卖出等）

需要适应的（变化）：
⚡ 股票代码格式：000001 → 000001.XSHE
⚡ 日期格式：20240101 → 2024-01-01
⚡ 列名：收盘 → close
⚡ 数据获取函数：ak.stock_zh_a_hist() → get_price()
⚡ 运行环境：本地Python → 聚宽平台

好消息是：
策略的核心逻辑完全相同，只是API调用方式变了！
"""

print(summary)

print("\n" + "=" * 80)
print("聚宽入门指南完成！")
print("=" * 80)
print("\n现在就去 https://www.joinquant.com/ 试试吧！")
