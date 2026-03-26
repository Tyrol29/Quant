"""
================================================================================
聚宽平台 - MACD金叉死叉策略（沪深300指数择时版）
================================================================================

策略说明：
- 信号来源：沪深300指数（000300.XSHG）
- 交易标的：华泰柏瑞沪深300ETF（510300.XSHG）
- 逻辑：用沪深300指数的MACD信号，交易沪深300ETF
- 资金：初始资金100万元
- 信号：指数MACD金叉全仓买入ETF，死叉全仓卖出ETF

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
- 计算沪深300指数的MACD指标作为择时信号
- 当指数出现金叉时，买入沪深300ETF
- 当指数出现死叉时，卖出沪深300ETF
- 实现对沪深300指数的择时交易

作者：量化投资学习
日期：2026-03-26
================================================================================
"""

import pandas as pd
import numpy as np

# ========== 全局配置 ==========
# 信号来源：沪深300指数
INDEX_CODE = '000300.XSHG'  # 沪深300指数

# 交易标的：华泰柏瑞沪深300ETF
ETF_CODE = '510300.XSHG'    # 沪深300ETF

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
    g.index_code = INDEX_CODE    # 信号来源：指数
    g.etf_code = ETF_CODE        # 交易标的：ETF
    g.fast_period = FAST_PERIOD
    g.slow_period = SLOW_PERIOD
    g.signal_period = SIGNAL_PERIOD
    
    # 记录交易统计
    g.trade_stats = {
        'total_trades': 0,       # 总交易次数
        'buy_trades': 0,         # 买入次数
        'sell_trades': 0,        # 卖出次数
        'last_signal': None      # 上一个信号
    }
    
    # 设置定时运行（每天开盘时运行）
    run_daily(trade, time='open')
    
    # 设置收盘后记录
    run_daily(after_market_close, time='after_close')
    
    log.info(f"策略初始化完成")
    log.info(f"信号来源: {g.index_code} (沪深300指数)")
    log.info(f"交易标的: {g.etf_code} (沪深300ETF)")
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
    - 获取沪深300指数的历史价格数据
    - 计算指数的MACD指标作为择时信号
    - 指数金叉：买入沪深300ETF
    - 指数死叉：卖出沪深300ETF
    """
    index_code = g.index_code    # 指数（信号来源）
    etf_code = g.etf_code        # ETF（交易标的）
    
    try:
        # 获取沪深300指数的历史数据（用于计算信号）
        index_hist = attribute_history(
            index_code, 
            count=60,           # 获取60天数据
            unit='1d',          # 日线
            fields=['close'],   # 只需要收盘价
            skip_paused=True,   # 跳过停牌
            df=False            # 返回dict格式
        )
        
        if index_hist is None or len(index_hist['close']) < 35:
            log.warning(f"{index_code} 数据不足，跳过交易")
            return
        
        # 计算指数的MACD（作为择时信号）
        macd_data = calculate_macd(
            index_hist['close'], 
            fast=g.fast_period, 
            slow=g.slow_period, 
            signal=g.signal_period
        )
        
        # 获取当前ETF持仓
        position = context.portfolio.positions.get(etf_code)
        current_amount = position.total_amount if position else 0
        
        # 获取ETF当前价格
        etf_data = get_current_data()[etf_code]
        if etf_data.paused:
            log.info(f"{etf_code} 停牌，跳过交易")
            return
        
        etf_price = etf_data.day_open
        
        # 判断指数的金叉死叉
        is_golden_cross = (macd_data['DIF'] > macd_data['DEA']) and \
                         (macd_data['prev_DIF'] <= macd_data['prev_DEA'])
        
        is_death_cross = (macd_data['DIF'] < macd_data['DEA']) and \
                        (macd_data['prev_DIF'] >= macd_data['prev_DEA'])
        
        # 指数金叉 -> 买入ETF（全仓）
        if is_golden_cross and current_amount == 0:
            # 计算可买入数量（全仓，100股整数倍）
            cash = context.portfolio.available_cash
            amount = int(cash / etf_price / 100) * 100
            
            if amount > 0:
                order(etf_code, amount)
                g.trade_stats['buy_trades'] += 1
                g.trade_stats['total_trades'] += 1
                g.trade_stats['last_signal'] = '金叉买入'
                
                log.info(f"【指数金叉】{index_code} DIF上穿DEA")
                log.info(f"【买入ETF】{etf_code} {amount}股 @ {etf_price:.3f}")
                log.info(f"         指数DIF={macd_data['DIF']:.4f}, DEA={macd_data['DEA']:.4f}")
        
        # 指数死叉 -> 卖出ETF（全仓）
        elif is_death_cross and current_amount > 0:
            # 清仓
            order_target(etf_code, 0)
            g.trade_stats['sell_trades'] += 1
            g.trade_stats['total_trades'] += 1
            g.trade_stats['last_signal'] = '死叉卖出'
            
            log.info(f"【指数死叉】{index_code} DIF下穿DEA")
            log.info(f"【卖出ETF】{etf_code} {current_amount}股 @ {etf_price:.3f}")
            log.info(f"         指数DIF={macd_data['DIF']:.4f}, DEA={macd_data['DEA']:.4f}")
        
        # 持有期间判断（可选：记录持仓状态）
        elif current_amount > 0:
            # 当前持有ETF，判断指数是否仍处于多头区域
            if macd_data['DIF'] > macd_data['DEA']:
                # DIF在DEA上方，多头趋势继续
                pass
            else:
                # DIF在DEA下方，但还未死叉（震荡区）
                pass
            
    except Exception as e:
        log.error(f"交易执行出错: {e}")
        import traceback
        log.error(traceback.format_exc())


def after_market_close(context):
    """
    收盘后运行：记录账户信息和交易统计
    """
    etf_code = g.etf_code
    index_code = g.index_code
    
    # 获取当前ETF持仓
    position = context.portfolio.positions.get(etf_code)
    current_amount = position.total_amount if position else 0
    position_value = position.value if position else 0
    
    # 账户信息
    available_cash = context.portfolio.available_cash
    total_value = context.portfolio.total_value
    
    # 计算收益率
    returns = context.portfolio.returns
    total_returns = (total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL
    
    # 获取指数当日收盘价（用于对比）
    try:
        index_price = get_price(index_code, count=1, end_date=context.current_dt, 
                                frequency='1d', fields=['close'], panel=False)['close'].iloc[-1]
    except:
        index_price = None
    
    # 记录账户信息
    log.info('========================================')
    log.info(f'日期: {context.current_dt.strftime("%Y-%m-%d")}')
    log.info(f'沪深300指数: {index_price:.2f}' if index_price else '沪深300指数: 无数据')
    log.info(f'总资产: {total_value:,.2f}')
    log.info(f'持仓市值: {position_value:,.2f}')
    log.info(f'持仓ETF: {current_amount}股')
    log.info(f'可用现金: {available_cash:,.2f}')
    log.info(f'当日收益率: {returns*100:.2f}%')
    log.info(f'累计收益率: {total_returns*100:.2f}%')
    log.info(f'交易统计: 买入{g.trade_stats["buy_trades"]}次 / 卖出{g.trade_stats["sell_trades"]}次')
    if g.trade_stats['last_signal']:
        log.info(f'最近信号: {g.trade_stats["last_signal"]}')
    log.info('========================================')


# ========== 策略说明 ==========
"""
【策略名称】MACD指数择时策略（沪深300指数版）

【策略核心思想】
- 通过沪深300指数的MACD指标判断市场趋势
- 当指数出现金叉时，认为市场进入上升趋势，买入ETF
- 当指数出现死叉时，认为市场进入下降趋势，卖出ETF空仓
- 实现对大盘指数的择时交易，避开下跌趋势，参与上升趋势

【信号来源 vs 交易标的】
┌─────────────────┬────────────────────────────────────────┐
│     角色        │               代码/说明                │
├─────────────────┼────────────────────────────────────────┤
│ 信号来源        │ 000300.XSHG（沪深300指数）             │
│ 交易标的        │ 510300.XSHG（华泰柏瑞沪深300ETF）      │
├─────────────────┼────────────────────────────────────────┤
│ 关系            │ 用指数MACD信号指导ETF交易              │
│ 原理            │ ETF紧密跟踪指数，指数信号≈ETF信号      │
└─────────────────┴────────────────────────────────────────┘

【为什么选择指数作为信号源？】
1. 指数比个股更稳定，MACD信号更可靠
2. 指数代表整体市场趋势，不易被个股操纵
3. ETF紧密跟踪指数，指数信号能有效指导ETF交易
4. 避免个股停牌、财报等事件干扰

【MACD计算公式】
- DIF = EMA(12) - EMA(26)
- DEA = EMA(DIF, 9)  
- MACD柱状图 = (DIF - DEA) × 2

【交易规则】
- 初始资金：100万元
- 信号来源：000300.XSHG（沪深300指数）
- 交易标的：510300.XSHG（沪深300ETF）
- 买入信号：指数MACD金叉，全仓买入ETF
- 卖出信号：指数MACD死叉，全仓卖出ETF空仓
- 交易单位：100股（1手）整数倍

【交易成本】
- 买入佣金：万分之三，最低5元
- 卖出佣金：万分之三，最低5元
- ETF无印花税
- 滑点：0.1%

【回测设置建议】
- 时间范围：2024-01-01 至 2026-03-26（近两年）
- 初始资金：1000000元（100万）
- 回测频率：每天
- Benchmark：000300.XSHG（沪深300指数）

【与ETF直接版对比】
┌─────────────────┬──────────────────┬──────────────────┐
│     项目        │   ETF直接版      │  指数择时版      │
├─────────────────┼──────────────────┼──────────────────┤
│ 信号来源        │ ETF价格          │ 沪深300指数      │
│ 交易标的        │ 沪深300ETF       │ 沪深300ETF       │
│ 信号稳定性      │ 一般             │ 更好             │
│ 与指数相关性    │ 高               │ 更高             │
│ 策略逻辑        │ ETF自身MACD      │ 指数MACD指导ETF  │
└─────────────────┴──────────────────┴──────────────────┘

【策略优势】
1. 信号更稳定：指数比ETF更平滑，MACD信号更可靠
2. 趋势明确：捕捉市场整体趋势，避免个股波动干扰
3. 成本低：ETF交易无印花税，适合择时交易
4. 流动性好：沪深300ETF是市场规模最大的ETF
5. 简单直观：经典的指数择时策略

【策略局限】
1. 滞后性：MACD是趋势指标，信号有一定滞后
2. 震荡市表现差：横盘震荡时会出现频繁交易
3. 无法跑赢指数：只能跟随指数，不能超越指数
4. 空仓期无收益：死叉后空仓，可能错过后续上涨

【改进方向】
1. 加入均线过滤：如只在指数站稳60日均线上方才做多
2. 分批建仓：金叉后分3次买入，降低择时风险
3. 动态仓位：根据MACD柱状图强度调整仓位比例
4. 多指标共振：结合RSI、成交量等指标过滤信号
5. 加入止损：当回撤超过一定比例时强制止损

【查看指标】
回测完成后可查看：
1. 累计收益率（与沪深300指数对比）
2. 年化收益率、最大回撤、夏普比率
3. Beta（相对于沪深300的系统性风险）
4. Alpha（超额收益）
5. 胜率、盈亏比
6. 详细的交易记录

【策略适用场景】
- 适合：趋势明显的市场（牛市或熊市）
- 不适合：震荡市、横盘整理阶段
- 建议：结合宏观经济周期使用，长周期择时效果更好
"""
