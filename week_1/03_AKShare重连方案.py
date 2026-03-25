"""
================================================================================
AKShare 智能重连方案
当遇到 RemoteDisconnected 时的终极解决方案
================================================================================
"""

import akshare as ak
import pandas as pd
import time
import random
from datetime import datetime, timedelta

print("=" * 80)
print("AKShare 智能重连方案")
print("=" * 80)


# ================================================================================
# 方案1：超长等待 + 多次重试
# ================================================================================

def get_data_with_patience(func, max_retries=10, base_delay=5, *args, **kwargs):
    """
    超耐心版本的数据获取函数
    
    参数:
        func: AKShare函数
        max_retries: 最大重试次数（默认10次）
        base_delay: 基础等待时间（默认5秒）
    """
    for attempt in range(max_retries):
        try:
            # 每次重试增加等待时间（指数退避）
            if attempt > 0:
                wait_time = base_delay * (1.5 ** (attempt - 1)) + random.uniform(1, 5)
                wait_time = min(wait_time, 60)  # 最多等60秒
                print(f"  第{attempt}次失败，等待 {wait_time:.1f} 秒后重试...")
                time.sleep(wait_time)
            
            print(f"  第{attempt + 1}次尝试...")
            result = func(*args, **kwargs)
            
            if attempt > 0:
                print(f"  ✓ 第{attempt + 1}次尝试成功！")
            else:
                print(f"  ✓ 成功！")
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "RemoteDisconnected" in error_msg or "Connection" in error_msg:
                print(f"    连接被拒绝，继续重试...")
            else:
                print(f"    其他错误: {error_msg[:50]}")
                raise  # 非网络错误直接抛出
    
    print(f"\n✗ 重试{max_retries}次后仍然失败")
    return None


# ================================================================================
# 方案2：使用不同时间尝试（东方财富可能某些时段限流）
# ================================================================================

print("\n" + "=" * 80)
print("【测试】获取平安银行历史数据（耐心模式）")
print("=" * 80)

print("\n提示：如果一直失败，可能是：")
print("1. 东方财富网站正在维护")
print("2. 当前时段限流严格（交易时间段9:30-15:00限流较严）")
print("3. 你的IP被暂时拉黑（24小时后自动恢复）")
print("4. 建议：晚上21:00后或早上8:00前尝试\n")

# 尝试获取数据
print("开始获取数据...")
df = get_data_with_patience(
    ak.stock_zh_a_hist,
    max_retries=5,
    base_delay=3,
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)

if df is not None:
    print(f"\n✓ 成功获取 {len(df)} 条数据")
    print(df.head())
else:
    print("\n✗ 获取失败，启用备用方案...")


# ================================================================================
# 方案3：使用代理（如果你有代理的话）
# ================================================================================

print("\n" + "=" * 80)
print("【方案3】使用代理IP（如果你有代理）")
print("=" * 80)

def set_proxy(http_proxy=None, https_proxy=None):
    """
    设置代理
    
    参数:
        http_proxy: HTTP代理，如 "http://127.0.0.1:7890"
        https_proxy: HTTPS代理，如 "http://127.0.0.1:7890"
    """
    import os
    
    if http_proxy:
        os.environ['HTTP_PROXY'] = http_proxy
        os.environ['http_proxy'] = http_proxy
    if https_proxy:
        os.environ['HTTPS_PROXY'] = https_proxy
        os.environ['https_proxy'] = https_proxy
    
    print(f"代理设置完成: HTTP={http_proxy}, HTTPS={https_proxy}")


# 取消代理
def clear_proxy():
    """清除代理设置"""
    import os
    for key in ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
        if key in os.environ:
            del os.environ[key]
    print("代理已清除")


print("""
如果你有代理（如Clash、V2Ray等），可以取消下方注释使用：

    # 设置代理（根据你的代理软件修改端口）
    set_proxy("http://127.0.0.1:7890", "http://127.0.0.1:7890")
    
    # 获取数据
    df = ak.stock_zh_a_hist(symbol="000001", ...)
    
    # 用完清除代理
    clear_proxy()
""")


# ================================================================================
# 方案4：修改请求头（模拟浏览器）
# ================================================================================

print("\n" + "=" * 80)
print("【方案4】修改User-Agent（模拟浏览器）")
print("=" * 80)

def set_custom_headers():
    """
    修改请求头，模拟真实浏览器
    （需要修改AKShare源码，不推荐新手使用）
    """
    print("""
此方案需要修改AKShare源码，步骤如下：

1. 找到AKShare安装路径：
   python -c "import akshare; print(akshare.__file__)"
   
2. 找到 utils/request.py 文件

3. 在 requests.Session() 后添加 headers：

   session.headers.update({
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...'
   })

4. 保存后重新运行

注意：修改源码可能导致更新时冲突，建议备份
""")


set_custom_headers()


# ================================================================================
# 方案5：终极方案 - 等待一段时间后重试
# ================================================================================

print("\n" + "=" * 80)
print("【方案5】定时重试（设置定时任务，稍后自动运行）")
print("=" * 80)

def schedule_retry(wait_minutes=30):
    """
    等待一段时间后重试
    
    参数:
        wait_minutes: 等待分钟数
    """
    print(f"\n将在 {wait_minutes} 分钟后自动重试...")
    print("你可以：")
    print("1. 先学习其他内容（如Pandas数据处理）")
    print("2. 去注册聚宽账号")
    print("3. 喝杯咖啡休息一下\n")
    
    for remaining in range(wait_minutes, 0, -1):
        print(f"\r  还剩 {remaining} 分钟...", end='', flush=True)
        time.sleep(60)  # 每分钟打印一次
    
    print("\n时间到，开始重试...")
    return True


# 如果需要定时重试，取消下方注释
# schedule_retry(wait_minutes=5)


# ================================================================================
# 快速检测网络状态
# ================================================================================

print("\n" + "=" * 80)
print("【网络状态检测】")
print("=" * 80)

def check_network():
    """检测当前网络状况"""
    import urllib.request
    
    sites = [
        ("百度", "https://www.baidu.com"),
        ("新浪", "https://finance.sina.com.cn"),
        ("东方财富", "https://quote.eastmoney.com"),
    ]
    
    print("\n检测访问各个网站的速度：")
    for name, url in sites:
        try:
            start = time.time()
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0')
            urllib.request.urlopen(req, timeout=5)
            elapsed = time.time() - start
            print(f"  {name}: {elapsed:.2f}s ✓")
        except Exception as e:
            print(f"  {name}: ✗ ({str(e)[:30]})")


check_network()


# ================================================================================
# 最终建议
# ================================================================================

print("\n" + "=" * 80)
print("【最终建议】")
print("=" * 80)

final_advice = """
基于当前情况，建议你：

方案A：立即使用（推荐）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
运行 "02_离线数据方案.py"
- 使用模拟数据继续学习
- 代码逻辑与真实数据完全一致
- 等网络恢复后再切换到真实数据

方案B：等待恢复
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 东方财富限流通常24小时自动解除
- 建议明天早上8:00后再试
- 避开交易时间段（9:30-15:00）

方案C：更换数据源
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 注册Tushare（tushare.pro）
- 或使用Yahoo Finance（pip install yfinance）
- 或注册聚宽（www.joinquant.com）

方案D：检查网络环境
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 关闭VPN/代理（某些代理会导致问题）
- 或开启VPN/代理（某些地区需要）
- 切换网络（如手机热点）

当前最推荐：方案A（不耽误学习进度）
"""

print(final_advice)

print("\n" + "=" * 80)
print("运行完成")
print("=" * 80)
