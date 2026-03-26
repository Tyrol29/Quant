"""
================================================================================
聚宽平台 - MACD金叉死叉策略（沪深300ETF版）
================================================================================

策略说明：
- 标的：华泰柏瑞沪深300ETF（510300.XSHG）
- 资金：初始资金100万元
- 信号：MACD金叉全仓买入，死叉全仓卖出
- 回测周期：近两年

使用说明：
1. 登录 https://www.joinquant.com/
2. 点击"我的策略" -> "新建策略"
3. 复制本代码粘贴到策略编辑器
4. 设置回测参数：
   - 时间范围：2024-01-01 至 2026-03-26（或最新日期）
   - 初始资金：1000000元（100万）
   - 回测频率：每天
   - Benchmark：000300.XSHG（沪深300指数）
5. 点击"回测"运行

策略逻辑：
- 通过交易沪深300ETF来跟踪沪深300指数表现
- 在指数上使用MACD金叉死叉信号进行择时交易

作者：量化投资学习
日期：2026-03-26
================================================================================
"""

import pandas as pd
import numpy as np

# ========== 全局配置 ==========
# 交易标的：华泰柏瑞沪深300ETF
SECURITY = '510300.XSHG'  # 沪深300ETF

# MACD参数
FAST_PERIOD = 12   # 快线周期
SLOW_PERIOD = 26   # 慢线周期
SIGNAL_PERIOD = 9  # 信号线周期

# 初始资金（元）
INITIAL_CAPITAL = 1000000


def initialize(context):
    """
    初始化函数，只运行一次
    """
    # 设置基准（沪深300指数）
    set_benchmark('000300.XSHG')
    
    # 设置佣金和印花税（ETF交易没有印花税）
    set_order_cost(OrderCost(
        open_tax=0,                 # ETF买入无印花税
        close_tax=0,                # ETF卖出无印花税
        open_commission=0.0003,     # 买入佣金（万分之三）
        close_commission=0.0003,    # 卖出佣金
        close_today_commission=0,   # 平今佣金
        min_commission=5            # 最低佣金5元
    ), type='stock')
    
    # 设置滑点
    set_slippage(FixedSlippage(0.001))  # 固定滑点0.1%
    
    # 保存配置到全局变量
    g.security = SECURITY
    g.fast_period = FAST_PERIOD
    g.slow_period = SLOW_PERIOD
    g.signal_period = SIGNAL_PERIOD
    
    # 记录交易统计
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
    
    log.info(f"策略初始化完成")
    log.info(f"交易标的: {g.security} (沪深300ETF)")
    log.info(f"MACD参数: 快线={g.fast_period}, 慢线={g.slow_period}, 信号={g.signal_period}")


def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    
    参数:
        close_prices: Series or list，收盘价序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    返回:
        dict: {'DIF': float, 'DEA': float, 'MACD': float, 'prev_DIF': float, 'prev_DEA': float}
    """
    # 转换为pandas Series
    if not isinstance(close_prices, pd.Series):
        close_prices = pd.Series(close_prices)
    
    # 计算EMA
    ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
    ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
    
    # DIF (快线) = 12日EMA - 26日EMA
    dif_series = ema_fast - ema_slow
    dif = dif_series.iloc[-1]
    
    # DEA (慢线/信号线) = DIF的9日EMA
    dea_series = dif_series.ewm(span=signal, adjust=False).mean()
    dea = dea_series.iloc[-1]
    
    # MACD柱状图 = (DIF - DEA) * 2
    macd = (dif - dea) * 2
    
    # 前一日DIF和DEA（用于判断金叉死叉）
    if len(dif_series) >= 2:
        prev_dif = dif_series.iloc[-2]
        prev_dea = dea_series.iloc[-2]
    else:
        prev_dif = dif
        prev_dea = dea
    
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
    
    策略逻辑：
    - 计算沪深300ETF的MACD指标
    - 金叉（DIF上穿DEA）：全仓买入
    - 死叉（DIF下穿DEA）：全仓卖出
    """
    security = g.security
    
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
            log.warning(f"{security} 数据不足，跳过交易")
            return
        
        # 计算MACD
        macd_data = calculate_macd(
            hist['close'], 
            fast=g.fast_period, 
            slow=g.slow_period, 
            signal=g.signal_period
        )
        
        # 获取当前持仓
        position = context.portfolio.positions.get(security)
        current_amount = position.total_amount if position else 0
        
        # 获取当前价格
        current_data = get_current_data()[security]
        if current_data.paused:
            log.info(f"{security} 停牌，跳过交易")
            return
        
        current_price = current_data.day_open
        
        # 判断金叉死叉
        is_golden_cross = (macd_data['DIF'] > macd_data['DEA']) and \
                         (macd_data['prev_DIF'] <= macd_data['prev_DEA'])
        
        is_death_cross = (macd_data['DIF'] < macd_data['DEA']) and \
                        (macd_data['prev_DIF'] >= macd_data['prev_DEA'])
        
        # 金叉买入 - 全仓买入
        if is_golden_cross and current_amount == 0:
            # 计算可买入数量（全仓，100股整数倍）
            cash = context.portfolio.available_cash
            amount = int(cash / current_price / 100) * 100
            
            if amount > 0:
                order(security, amount)
                g.trade_stats['buy_trades'] += 1
                g.trade_stats['total_trades'] += 1
                g.trade_stats['trade_log'].append({
                    'date': context.current_dt.strftime('%Y-%m-%d'),
                    'security': security,
                    'action': '买入',
                    'price': current_price,
                    'amount': amount,
                    'macd': macd_data['MACD'],
                    'dif': macd_data['DIF'],
                    'dea': macd_data['DEA']
                })
                log.info(f"【金叉买入】{security} {amount}股 @ {current_price:.3f}")
                log.info(f"         DIF={macd_data['DIF']:.4f}, DEA={macd_data['DEA']:.4f}, MACD={macd_data['MACD']:.4f}")
        
        # 死叉卖出 - 全仓卖出
        elif is_death_cross and current_amount > 0:
            # 清仓
            order_target(security, 0)
            g.trade_stats['sell_trades'] += 1
            g.trade_stats['total_trades'] += 1
            g.trade_stats['trade_log'].append({
                'date': context.current_dt.strftime('%Y-%m-%d'),
                'security': security,
                'action': '卖出',
                'price': current_price,
                'amount': current_amount,
                'macd': macd_data['MACD'],
                'dif': macd_data['DIF'],
                'dea': macd_data['DEA']
            })
            log.info(f"【死叉卖出】{security} {current_amount}股 @ {current_price:.3f}")
            log.info(f"         DIF={macd_data['DIF']:.4f}, DEA={macd_data['DEA']:.4f}, MACD={macd_data['MACD']:.4f}")
        
        # 记录当前状态（可选，每天记录一次）
        else:
            # 非交易信号日，只记录MACD状态
            pass
            
    except Exception as e:
        log.error(f"交易执行出错: {e}")
        import traceback
        log.error(traceback.format_exc())


def after_market_close(context):
    """
    收盘后运行：记录账户信息和交易统计
    """
    security = g.security
    
    # 获取当前持仓
    position = context.portfolio.positions.get(security)
    current_amount = position.total_amount if position else 0
    position_value = position.value if position else 0
    
    # 账户信息
    available_cash = context.portfolio.available_cash
    total_value = context.portfolio.total_value
    
    # 计算当日收益率
    returns = context.portfolio.returns
    
    # 计算累计收益率
    total_returns = (total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL
    
    # 记录账户信息
    log.info('========================================')
    log.info(f'日期: {context.current_dt.strftime("%Y-%m-%d")}')
    log.info(f'总资产: {total_value:,.2f}')
    log.info(f'持仓市值: {position_value:,.2f}')
    log.info(f'持仓股数: {current_amount}')
    log.info(f'可用现金: {available_cash:,.2f}')
    log.info(f'当日收益率: {returns*100:.2f}%')
    log.info(f'累计收益率: {total_returns*100:.2f}%')
    log.info(f'交易统计: 买入{g.trade_stats["buy_trades"]}次 / 卖出{g.trade_stats["sell_trades"]}次')
    log.info('========================================')


# ========== 策略说明 ==========
"""
【策略名称】MACD金叉死叉择时策略（沪深300ETF版）

【策略标的】
- 华泰柏瑞沪深300ETF（510300.XSHG）
- 该ETF紧密跟踪沪深300指数，是A股市场最具代表性的宽基指数ETF

【策略逻辑】
1. 获取沪深300ETF的历史价格数据
2. 计算MACD指标（DIF、DEA、MACD柱状图）
3. 当MACD金叉（DIF上穿DEA）时，全仓买入ETF
4. 当MACD死叉（DIF下穿DEA）时，全仓卖出ETF
5. 简单直接的择时策略，通过MACD捕捉指数的趋势性机会

【MACD计算公式】
- DIF = EMA(12) - EMA(26)
- DEA = EMA(DIF, 9)
- MACD柱状图 = (DIF - DEA) × 2

【交易规则】
- 初始资金：100万元
- 交易标的：510300.XSHG（沪深300ETF）
- 买入信号：MACD金叉，全仓买入
- 卖出信号：MACD死叉，全仓卖出
- 交易单位：100股（1手）整数倍

【交易成本】
- 买入佣金：万分之三，最低5元
- 卖出佣金：万分之三，最低5元
- ETF无印花税（相比股票交易成本低）
- 滑点：0.1%

【回测设置建议】
- 时间范围：2024-01-01 至 2026-03-26（近两年）
- 初始资金：1000000元（100万）
- 回测频率：每天
- Benchmark：000300.XSHG（沪深300指数）

【策略优势】
1. 交易成本低：ETF无印花税，适合频繁交易
2. 流动性好：沪深300ETF是市场规模最大的ETF之一
3. 分散风险：一键投资沪深300指数，分散个股风险
4. 简单直观：基于经典的MACD指标，逻辑清晰

【策略局限】
1. 震荡市表现可能不佳（MACD的通病）
2. 滞后性：MACD是趋势指标，信号有一定滞后
3. 单一标的：无法通过多标的分散波动

【与多股策略对比】
┌─────────────────┬──────────────────┬──────────────────┐
│     项目        │   多股MACD策略   │  沪深300ETF策略  │
├─────────────────┼──────────────────┼──────────────────┤
│ 标的数量        │ 40只股票         │ 1只ETF           │
│ 资金分配        │ 每只股票15万     │ 全仓100万        │
│ 交易成本        │ 较高（有印花税） │ 较低（无印花税） │
│ 风险分散        │ 好（多标的）     │ 一般（单一标的） │
│ 管理复杂度      │ 高               │ 低               │
│ 跟踪指数        │ 部分跟踪         │ 紧密跟踪         │
└─────────────────┴──────────────────┴──────────────────┘

【查看指标】
回测完成后可查看：
1. 累计收益率（与沪深300指数对比）
2. 年化收益率
3. 最大回撤
4. 夏普比率
5. 胜率（盈利交易次数 / 总交易次数）
6. 盈亏比（平均盈利 / 平均亏损）
7. Beta（相对于沪深300的系统性风险）
8. Alpha（超额收益）
9. 详细的交易记录和持仓记录

【改进方向】
1. 加入止损机制：当回撤超过一定比例时强制止损
2. 加入仓位管理：根据MACD柱状图强度调整仓位
3. 多周期共振：同时使用日线和周线MACD确认信号
4. 结合其他指标：如RSI、布林带等过滤假信号
5. 加入趋势判断：只在上升趋势中做多，下降趋势中空仓
"""
