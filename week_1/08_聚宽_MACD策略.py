"""
================================================================================
聚宽平台 - MACD金叉死叉策略
================================================================================

策略说明：
- 标的：沪深300成分股中市值前40的股票
- 资金：每只股票初始资金15万元
- 信号：MACD金叉买入，死叉卖出
- 回测周期：近两年

使用说明：
1. 登录 https://www.joinquant.com/
2. 点击"我的策略" -> "新建策略"
3. 复制本代码粘贴到策略编辑器
4. 设置回测参数：
   - 时间范围：2024-01-01 至 2025-12-31（或最新日期）
   - 初始资金：6000000元（600万，40只股票×15万）
   - 回测频率：每天
   - Benchmark：000300.XSHG（沪深300指数）
5. 点击"回测"运行

作者：量化投资学习
日期：2026-03-26
================================================================================
"""

import pandas as pd
import numpy as np

# ========== 全局配置 ==========
# 沪深300市值前40的股票（聚宽代码格式）
STOCK_POOL = [
    '600519.XSHG',  # 贵州茅台
    '300750.XSHE',  # 宁德时代
    '601318.XSHG',  # 中国平安
    '600036.XSHG',  # 招商银行
    '000858.XSHE',  # 五粮液
    '601012.XSHG',  # 隆基绿能
    '000333.XSHE',  # 美的集团
    '002594.XSHE',  # 比亚迪
    '600900.XSHG',  # 长江电力
    '600276.XSHG',  # 恒瑞医药
    '000568.XSHE',  # 泸州老窖
    '601888.XSHG',  # 中国中免
    '002415.XSHE',  # 海康威视
    '600309.XSHG',  # 万华化学
    '000002.XSHE',  # 万科A
    '601398.XSHG',  # 工商银行
    '600887.XSHG',  # 伊利股份
    '600438.XSHG',  # 通威股份
    '002142.XSHE',  # 宁波银行
    '300059.XSHE',  # 东方财富
    '600016.XSHG',  # 民生银行
    '000001.XSHE',  # 平安银行
    '600030.XSHG',  # 中信证券
    '601166.XSHG',  # 兴业银行
    '601288.XSHG',  # 农业银行
    '600031.XSHG',  # 三一重工
    '601668.XSHG',  # 中国建筑
    '601088.XSHG',  # 中国神华
    '000651.XSHE',  # 格力电器
    '600809.XSHG',  # 山西汾酒
    '601899.XSHG',  # 紫金矿业
    '300124.XSHE',  # 汇川技术
    '002352.XSHE',  # 顺丰控股
    '601985.XSHG',  # 中国核电
    '600104.XSHG',  # 上汽集团
    '600436.XSHG',  # 片仔癀
    '300274.XSHE',  # 阳光电源
    '601939.XSHG',  # 建设银行
    '002812.XSHE',  # 恩捷股份
    '600585.XSHG',  # 海螺水泥
]

# MACD参数
FAST_PERIOD = 12   # 快线周期
SLOW_PERIOD = 26   # 慢线周期
SIGNAL_PERIOD = 9  # 信号线周期

# 每只股票资金（元）
CAPITAL_PER_STOCK = 150000


def initialize(context):
    """
    初始化函数，只运行一次
    """
    # 设置基准
    set_benchmark('000300.XSHG')  # 沪深300指数
    
    # 设置佣金和印花税
    set_order_cost(OrderCost(
        open_tax=0,                 # 买入印花税
        close_tax=0.001,            # 卖出印花税（千分之一）
        open_commission=0.0003,     # 买入佣金（万分之三）
        close_commission=0.0003,    # 卖出佣金
        close_today_commission=0,   # 平今佣金
        min_commission=5            # 最低佣金5元
    ), type='stock')
    
    # 设置滑点
    set_slippage(FixedSlippage(0.002))  # 固定滑点0.2%
    
    # 保存股票池到全局变量
    g.stock_pool = STOCK_POOL
    g.capital_per_stock = CAPITAL_PER_STOCK
    
    # 记录每只股票的MACD状态
    # key: 股票代码, value: {'dif': float, 'dea': float, 'position': int}
    g.macd_status = {}
    
    # 记录回测统计
    g.trade_stats = {
        'total_trades': 0,      # 总交易次数
        'buy_trades': 0,        # 买入次数
        'sell_trades': 0,       # 卖出次数
        'trade_log': []         # 交易日志
    }
    
    # 设置定时运行（每天开盘时运行）
    run_daily(trade, time='open')
    
    # 设置收盘后记录
    run_daily(after_market_close, time='after_close')
    
    log.info(f"策略初始化完成，股票池数量: {len(g.stock_pool)}")


def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    
    参数:
        close_prices: Series or list，收盘价序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    返回:
        dict: {'DIF': float, 'DEA': float, 'MACD': float}
    """
    # 转换为pandas Series
    if not isinstance(close_prices, pd.Series):
        close_prices = pd.Series(close_prices)
    
    # 计算EMA
    ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
    ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
    
    # DIF (快线)
    dif = ema_fast.iloc[-1] - ema_slow.iloc[-1]
    
    # DEA (慢线/信号线)
    dea_series = (ema_fast - ema_slow).ewm(span=signal, adjust=False).mean()
    dea = dea_series.iloc[-1]
    
    # MACD柱状图
    macd = (dif - dea) * 2
    
    # 前一日DIF和DEA（用于判断金叉死叉）
    prev_dif = (ema_fast - ema_slow).iloc[-2] if len(close_prices) >= 2 else dif
    prev_dea = dea_series.iloc[-2] if len(dea_series) >= 2 else dea
    
    return {
        'DIF': dif,
        'DEA': dea,
        'MACD': macd,
        'prev_DIF': prev_dif,
        'prev_DEA': prev_dea
    }


def trade(context):
    """
    交易函数，每天开盘时运行
    """
    for security in g.stock_pool:
        try:
            # 获取历史数据（需要足够的数据计算MACD）
            # 获取60天数据，确保有足够的历史数据计算EMA
            hist = attribute_history(
                security, 
                count=60,           # 获取60天数据
                unit='1d',          # 日线
                fields=['close'],   # 只需要收盘价
                skip_paused=True,   # 跳过停牌
                df=False            # 返回dict格式
            )
            
            if hist is None or len(hist['close']) < 35:
                # 数据不足，跳过
                continue
            
            # 计算MACD
            macd_data = calculate_macd(
                hist['close'], 
                fast=FAST_PERIOD, 
                slow=SLOW_PERIOD, 
                signal=SIGNAL_PERIOD
            )
            
            # 获取当前持仓
            position = context.portfolio.positions.get(security)
            current_amount = position.total_amount if position else 0
            
            # 获取当前价格
            current_data = get_current_data()[security]
            if current_data.paused:
                continue  # 停牌跳过
            
            current_price = current_data.day_open
            
            # 判断金叉死叉
            is_golden_cross = (macd_data['DIF'] > macd_data['DEA']) and \
                             (macd_data['prev_DIF'] <= macd_data['prev_DEA'])
            
            is_death_cross = (macd_data['DIF'] < macd_data['DEA']) and \
                            (macd_data['prev_DIF'] >= macd_data['prev_DEA'])
            
            # 金叉买入
            if is_golden_cross and current_amount == 0:
                # 计算可买入数量（整手）
                cash = context.portfolio.available_cash
                # 每只股票的可用资金上限
                max_stock_cash = min(g.capital_per_stock, cash)
                amount = int(max_stock_cash / current_price / 100) * 100
                
                if amount > 0:
                    order(security, amount)
                    g.trade_stats['buy_trades'] += 1
                    g.trade_stats['total_trades'] += 1
                    g.trade_stats['trade_log'].append({
                        'date': context.current_dt.strftime('%Y-%m-%d'),
                        'security': security,
                        'action': '买入',
                        'price': current_price,
                        'amount': amount
                    })
                    log.info(f"【金叉买入】{security} {amount}股 @ {current_price:.2f}, DIF={macd_data['DIF']:.3f}, DEA={macd_data['DEA']:.3f}")
            
            # 死叉卖出
            elif is_death_cross and current_amount > 0:
                order_target(security, 0)  # 清仓
                g.trade_stats['sell_trades'] += 1
                g.trade_stats['total_trades'] += 1
                g.trade_stats['trade_log'].append({
                    'date': context.current_dt.strftime('%Y-%m-%d'),
                    'security': security,
                    'action': '卖出',
                    'price': current_price,
                    'amount': current_amount
                })
                log.info(f"【死叉卖出】{security} {current_amount}股 @ {current_price:.2f}, DIF={macd_data['DIF']:.3f}, DEA={macd_data['DEA']:.3f}")
                
        except Exception as e:
            log.error(f"处理 {security} 时出错: {e}")
            continue


def after_market_close(context):
    """
    收盘后运行：记录账户信息和交易统计
    """
    # 计算当前持仓数量和市值
    positions = context.portfolio.positions
    position_count = len(positions)
    positions_value = context.portfolio.positions_value
    available_cash = context.portfolio.available_cash
    total_value = context.portfolio.total_value
    
    # 计算当日收益率
    returns = context.portfolio.returns
    
    # 记录账户信息
    log.info('========================================')
    log.info(f'日期: {context.current_dt.strftime("%Y-%m-%d")}')
    log.info(f'总资产: {total_value:,.2f}')
    log.info(f'持仓市值: {positions_value:,.2f}')
    log.info(f'可用现金: {available_cash:,.2f}')
    log.info(f'持仓股票数: {position_count}/{len(g.stock_pool)}')
    log.info(f'当日收益率: {returns*100:.2f}%')
    log.info(f'累计交易次数: 买入{g.trade_stats["buy_trades"]}次 / 卖出{g.trade_stats["sell_trades"]}次')
    log.info('========================================')


# ========== 策略说明 ==========
"""
【策略名称】MACD金叉死叉策略

【策略逻辑】
1. 选择沪深300市值前40的股票作为股票池
2. 对每只股票单独计算MACD指标
3. MACD金叉（DIF上穿DEA）时，使用15万元资金全仓买入
4. MACD死叉（DIF下穿DEA）时，全仓卖出
5. 每只股票独立交易，互不影响

【MACD参数】
- 快线周期（DIF）：12日
- 慢线周期（DEA）：26日
- 信号线周期：9日

【资金管理】
- 初始资金：600万元（40只股票 × 15万元）
- 单只股票上限：15万元
- 交易单位：100股（1手）整数倍

【交易成本】
- 买入佣金：万分之三，最低5元
- 卖出佣金：万分之三，最低5元
- 卖出印花税：千分之一
- 滑点：0.2%

【回测设置建议】
- 时间范围：2024-01-01 至 2026-03-26（近两年）
- 初始资金：6000000元
- 回测频率：每天
- Benchmark：000300.XSHG（沪深300指数）

【查看指标】
回测完成后可查看：
1. 累计收益率
2. 年化收益率
3. 最大回撤
4. 夏普比率
5. 胜率
6. 盈亏比
7. 每日交易记录
"""
