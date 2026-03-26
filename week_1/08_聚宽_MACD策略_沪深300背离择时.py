"""
================================================================================
聚宽平台 - MACD顶底背离择时策略（沪深300ETF版）
================================================================================

策略说明：
- 信号来源：沪深300指数（000300.XSHG）
- 交易标的：华泰柏瑞沪深300ETF（510300.XSHG）
- 信号逻辑：
  * 底背离（价格新低，MACD未新低）：全仓买入
  * 顶背离（价格新高，MACD未新高）：全仓卖出
- 资金：初始资金100万元

背离定义：
- 顶背离：指数价格创出近期新高，但MACD柱状图（或DIF）未创出新高
- 底背离：指数价格创出近期新低，但MACD柱状图（或DIF）未创出新低

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

# 背离检测参数
DIVERGENCE_WINDOW = 20  # 检测背离的窗口期（天数）

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
    g.divergence_window = DIVERGENCE_WINDOW
    
    # 记录交易统计
    g.trade_stats = {
        'total_trades': 0,       # 总交易次数
        'buy_trades': 0,         # 买入次数（底背离）
        'sell_trades': 0,        # 卖出次数（顶背离）
        'last_signal': None,     # 上一个信号
        'divergence_log': []     # 背离记录
    }
    
    # 记录历史数据用于背离检测
    g.price_history = []       # 价格历史
    g.macd_history = []        # MACD历史
    
    # 设置定时运行（每天开盘时运行）
    run_daily(trade, time='open')
    
    # 设置收盘后记录
    run_daily(after_market_close, time='after_close')
    
    log.info(f"策略初始化完成")
    log.info(f"信号来源: {g.index_code} (沪深300指数)")
    log.info(f"交易标的: {g.etf_code} (沪深300ETF)")
    log.info(f"背离检测窗口: {g.divergence_window}天")


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
    if not isinstance(close_prices, pd.Series):
        close_prices = pd.Series(close_prices)
    
    # 计算EMA
    ema_fast = close_prices.ewm(span=fast, adjust=False).mean()
    ema_slow = close_prices.ewm(span=slow, adjust=False).mean()
    
    # DIF
    dif = ema_fast - ema_slow
    
    # DEA
    dea = dif.ewm(span=signal, adjust=False).mean()
    
    # MACD柱状图
    macd = (dif - dea) * 2
    
    return {
        'DIF': dif,
        'DEA': dea,
        'MACD': macd
    }


def detect_divergence(prices, macd_values, window=20):
    """
    检测顶背离和底背离
    
    参数:
        prices: 价格序列（最近的N天）
        macd_values: MACD柱状图序列
        window: 检测窗口
    
    返回:
        dict: {
            'top_divergence': bool,    # 是否顶背离
            'bottom_divergence': bool, # 是否底背离
            'description': str         # 描述
        }
    """
    if len(prices) < window or len(macd_values) < window:
        return {'top_divergence': False, 'bottom_divergence': False, 'description': '数据不足'}
    
    # 取最近window天的数据
    recent_prices = prices[-window:]
    recent_macd = macd_values[-window:]
    
    # 当前值
    current_price = recent_prices[-1]
    current_macd = recent_macd[-1]
    
    # 找到窗口期内的价格极值和对应的MACD
    max_price_idx = np.argmax(recent_prices)
    min_price_idx = np.argmin(recent_prices)
    max_price = recent_prices[max_price_idx]
    min_price = recent_prices[min_price_idx]
    max_price_macd = recent_macd[max_price_idx]
    min_price_macd = recent_macd[min_price_idx]
    
    # 检测顶背离：当前价格接近窗口内最高点，但MACD没有同步新高
    # 条件：1) 当前价格是近期高点（在最高点的95%以上）
    #       2) 当前MACD低于窗口内最高MACD（背离）
    is_price_high = current_price >= max_price * 0.98  # 价格在最高点的98%以上
    is_macd_lower = current_macd < max_price_macd * 0.95  # MACD明显低于高点时的值
    
    top_divergence = is_price_high and is_macd_lower and (max_price_idx < len(recent_prices) - 1)
    
    # 检测底背离：当前价格接近窗口内最低点，但MACD没有同步新低
    # 条件：1) 当前价格是近期低点（在最低点的105%以下）
    #       2) 当前MACD高于窗口内最低MACD（背离）
    is_price_low = current_price <= min_price * 1.02  # 价格在最低点的102%以下
    is_macd_higher = current_macd > min_price_macd * 1.05  # MACD明显高于低点时的值
    
    bottom_divergence = is_price_low and is_macd_higher and (min_price_idx < len(recent_prices) - 1)
    
    description = ''
    if top_divergence:
        description = f'顶背离：价格{current_price:.2f}接近高点{max_price:.2f}，MACD从{max_price_macd:.4f}降至{current_macd:.4f}'
    elif bottom_divergence:
        description = f'底背离：价格{current_price:.2f}接近低点{min_price:.2f}，MACD从{min_price_macd:.4f}升至{current_macd:.4f}'
    
    return {
        'top_divergence': top_divergence,
        'bottom_divergence': bottom_divergence,
        'description': description,
        'current_price': current_price,
        'current_macd': current_macd,
        'max_price': max_price,
        'min_price': min_price,
        'max_price_macd': max_price_macd,
        'min_price_macd': min_price_macd
    }


def trade(context):
    """
    交易函数，每天开盘时运行
    
    策略逻辑：
    - 计算沪深300指数的MACD指标
    - 检测顶背离和底背离信号
    - 底背离：全仓买入ETF
    - 顶背离：全仓卖出ETF
    """
    index_code = g.index_code
    etf_code = g.etf_code
    
    try:
        # 获取沪深300指数的历史数据（需要足够的数据计算MACD和背离）
        # 获取90天数据，确保有足够的历史数据
        hist = attribute_history(
            index_code, 
            count=90,           # 获取90天数据
            unit='1d',          # 日线
            fields=['close'],   # 只需要收盘价
            skip_paused=True,   # 跳过停牌
            df=False            # 返回dict格式
        )
        
        if hist is None or len(hist['close']) < 60:
            log.warning(f"{index_code} 数据不足，跳过交易")
            return
        
        close_prices = pd.Series(hist['close'])
        
        # 计算MACD
        macd_data = calculate_macd(
            close_prices, 
            fast=g.fast_period, 
            slow=g.slow_period, 
            signal=g.signal_period
        )
        
        macd_values = macd_data['MACD'].values
        
        # 检测背离
        divergence = detect_divergence(
            close_prices.values, 
            macd_values, 
            window=g.divergence_window
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
        
        # 底背离买入信号
        if divergence['bottom_divergence'] and current_amount == 0:
            # 计算可买入数量（全仓，100股整数倍）
            cash = context.portfolio.available_cash
            amount = int(cash / etf_price / 100) * 100
            
            if amount > 0:
                order(etf_code, amount)
                g.trade_stats['buy_trades'] += 1
                g.trade_stats['total_trades'] += 1
                g.trade_stats['last_signal'] = '底背离买入'
                g.trade_stats['divergence_log'].append({
                    'date': context.current_dt.strftime('%Y-%m-%d'),
                    'type': '底背离',
                    'price': divergence['current_price'],
                    'macd': divergence['current_macd'],
                    'description': divergence['description']
                })
                
                log.info(f"【底背离买入】{etf_code} {amount}股 @ {etf_price:.3f}")
                log.info(f"         {divergence['description']}")
        
        # 顶背离卖出信号
        elif divergence['top_divergence'] and current_amount > 0:
            # 清仓
            order_target(etf_code, 0)
            g.trade_stats['sell_trades'] += 1
            g.trade_stats['total_trades'] += 1
            g.trade_stats['last_signal'] = '顶背离卖出'
            g.trade_stats['divergence_log'].append({
                'date': context.current_dt.strftime('%Y-%m-%d'),
                'type': '顶背离',
                'price': divergence['current_price'],
                'macd': divergence['current_macd'],
                'description': divergence['description']
            })
            
            log.info(f"【顶背离卖出】{etf_code} {current_amount}股 @ {etf_price:.3f}")
            log.info(f"         {divergence['description']}")
        
        # 记录当前状态（用于调试）
        if divergence['top_divergence'] or divergence['bottom_divergence']:
            pass  # 已经在上面记录了
        else:
            # 无背离信号，记录MACD状态
            current_price = close_prices.iloc[-1]
            current_macd = macd_values[-1]
            max_price = divergence['max_price']
            min_price = divergence['min_price']
            
            # 如果价格接近极值但无背离，记录为观察
            if current_price >= max_price * 0.99:
                log.info(f"[观察] 价格接近高点{max_price:.2f}，MACD={current_macd:.4f}，无背离")
            elif current_price <= min_price * 1.01:
                log.info(f"[观察] 价格接近低点{min_price:.2f}，MACD={current_macd:.4f}，无背离")
            
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
    
    # 获取指数当日收盘价
    try:
        index_price = get_price(index_code, count=1, end_date=context.current_dt, 
                                frequency='1d', fields=['close'], panel=False)['close'].iloc[-1]
    except:
        index_price = None
    
    # 记录账户信息
    log.info('========================================')
    log.info(f'日期: {context.current_dt.strftime("%Y-%m-%d")}')
    if index_price:
        log.info(f'沪深300指数: {index_price:.2f}')
    log.info(f'总资产: {total_value:,.2f}')
    log.info(f'持仓市值: {position_value:,.2f}')
    log.info(f'持仓ETF: {current_amount}股')
    log.info(f'可用现金: {available_cash:,.2f}')
    log.info(f'当日收益率: {returns*100:.2f}%')
    log.info(f'累计收益率: {total_returns*100:.2f}%')
    log.info(f'交易统计: 买入(底背离){g.trade_stats["buy_trades"]}次 / 卖出(顶背离){g.trade_stats["sell_trades"]}次')
    if g.trade_stats['last_signal']:
        log.info(f'最近信号: {g.trade_stats["last_signal"]}')
    log.info('========================================')


# ========== 策略说明 ==========
"""
【策略名称】MACD顶底背离择时策略（沪深300ETF版）

【背离定义】
顶背离（卖出信号）：
- 指数价格创出近期新高
- 但MACD柱状图未创出新高（动能减弱）
- 预示上涨动能衰竭，可能见顶回落

底背离（买入信号）：
- 指数价格创出近期新低
- 但MACD柱状图未创出新低（动能增强）
- 预示下跌动能衰竭，可能见底反弹

【交易逻辑】
1. 获取沪深300指数历史数据
2. 计算MACD指标（DIF、DEA、MACD柱状图）
3. 检测顶背离和底背离信号
4. 底背离 → 买入沪深300ETF（全仓）
5. 顶背离 → 卖出沪深300ETF（空仓）

【背离检测算法】
在DIVERGENCE_WINDOW（默认20天）窗口内：
- 顶背离：当前价格≥窗口内最高价的98%，且当前MACD<最高MACD的95%
- 底背离：当前价格≤窗口内最低价的102%，且当前MACD>最低MACD的105%

【与金叉死叉策略对比】
┌─────────────────┬──────────────────┬──────────────────┐
│     项目        │   金叉死叉策略   │   背离策略       │
├─────────────────┼──────────────────┼──────────────────┤
│ 信号类型        │ 趋势跟随         │ 反转预测         │
│ 买入时机        │ 上涨中           │ 下跌末期         │
│ 卖出时机        │ 下跌中           │ 上涨末期         │
│ 滞后性          │ 较强             │ 较弱             │
│ 震荡市表现      │ 差（频繁交易）   │ 较好（信号少）   │
│ 信号频率        │ 高               │ 低               │
└─────────────────┴──────────────────┴──────────────────┘

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

【策略优势】
1. 反转预判：比金叉死叉更早识别顶部和底部
2. 信号质量：背离信号比交叉信号更可靠
3. 交易频率低：背离出现频率低于金叉死叉，减少交易成本
4. 风控效果好：顶背离卖出能避开大部分下跌

【策略局限】
1. 信号稀少：可能没有足够的交易机会
2. 假背离：震荡市中可能出现假背离信号
3. 需要确认：背离后可能不会立即反转，需要等待确认
4. 参数敏感：背离检测窗口期影响信号质量

【改进方向】
1. 多周期背离：日线背离+周线背离共振
2. 背离确认：背离出现后，等待价格突破确认
3. 分批交易：背离出现时部分建仓，确认后加仓
4. 结合支撑阻力：在关键支撑位寻找底背离
5. 量价背离：结合成交量背离提高信号质量

【查看指标】
回测完成后可查看：
1. 累计收益率（与沪深300指数对比）
2. 年化收益率、最大回撤、夏普比率
3. Beta、Alpha
4. 胜率、盈亏比
5. 详细的背离记录和交易记录
"""
