"""
================================================================================
AKShare 网络问题解决方案
处理 ConnectionError、RemoteDisconnected 等常见问题
================================================================================
"""

import akshare as ak
import pandas as pd
import time
import random
from datetime import datetime, timedelta


# ================================================================================
# 方案1：添加重试机制（推荐）
# ================================================================================

def safe_api_call(func, max_retries=3, delay=2, *args, **kwargs):
    """
    带重试机制的API调用
    
    参数:
        func: 要调用的函数
        max_retries: 最大重试次数
        delay: 每次重试的间隔秒数
    """
    for attempt in range(max_retries):
        try:
            # 随机延迟，避免被识别为机器人
            if attempt > 0:
                sleep_time = delay + random.uniform(0, 2)
                print(f"  第{attempt}次重试，等待{sleep_time:.1f}秒...")
                time.sleep(sleep_time)
            
            result = func(*args, **kwargs)
            if attempt > 0:
                print(f"  ✓ 第{attempt}次重试成功！")
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ 第{attempt + 1}次尝试失败: {error_msg[:50]}...")
            
            if attempt == max_retries - 1:
                print(f"  ✗ 已达到最大重试次数({max_retries})，放弃")
                raise
    
    return None


# ================================================================================
# 方案2：获取实时行情的改进版本
# ================================================================================

def get_realtime_quotes_safe(max_retries=3):
    """
    安全获取实时行情（带重试机制）
    """
    print("正在获取实时行情...")
    
    try:
        df = safe_api_call(
            ak.stock_zh_a_spot_em,
            max_retries=max_retries,
            delay=3
        )
        print(f"✓ 成功获取 {len(df)} 条实时行情数据")
        return df
    except Exception as e:
        print(f"✗ 获取实时行情失败: {e}")
        return None


# ================================================================================
# 方案3：获取历史数据的改进版本（更稳定）
# ================================================================================

def get_stock_history_safe(symbol="000001", days=60, max_retries=3):
    """
    安全获取历史数据（带重试机制）
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"正在获取 {symbol} 的历史数据...")
    
    try:
        df = safe_api_call(
            ak.stock_zh_a_hist,
            max_retries=max_retries,
            delay=2,
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"
        )
        print(f"✓ 成功获取 {len(df)} 条历史数据")
        return df
    except Exception as e:
        print(f"✗ 获取历史数据失败: {e}")
        return None


# ================================================================================
# 方案4：分批获取数据（降低被限流风险）
# ================================================================================

def get_stock_list_batch(batch_size=100, delay_between_batches=1):
    """
    分批获取股票列表（避免一次性请求过多）
    """
    print("正在分批获取股票列表...")
    
    try:
        df = safe_api_call(ak.stock_zh_a_spot_em, max_retries=3, delay=2)
        
        if df is not None:
            # 添加延时，避免后续操作过快
            time.sleep(delay_between_batches)
            return df
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None


# ================================================================================
# 方案5：使用备用数据源
# ================================================================================

def get_realtime_backup():
    """
    备用方案：使用新浪财经获取实时行情
    （当东方财富接口失败时使用）
    """
    print("尝试使用备用数据源（新浪财经）...")
    
    try:
        # 新浪财经接口通常更稳定
        df = ak.stock_zh_a_spot()
        print(f"✓ 备用数据源成功，获取 {len(df)} 条数据")
        return df
    except Exception as e:
        print(f"✗ 备用数据源也失败: {e}")
        return None


# ================================================================================
# 方案6：本地缓存机制
# ================================================================================

import json
import os

class DataCache:
    """数据缓存类，避免重复请求"""
    
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, key, max_age_minutes=5):
        """
        获取缓存数据
        
        参数:
            key: 缓存键
            max_age_minutes: 缓存最大有效期（分钟）
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        # 检查缓存是否过期
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if (datetime.now() - file_time).total_seconds() > max_age_minutes * 60:
            print(f"  缓存已过期（{key}）")
            return None
        
        # 读取缓存
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"  ✓ 使用缓存数据（{key}）")
            return pd.DataFrame(data)
        except:
            return None
    
    def set(self, key, df):
        """保存数据到缓存"""
        cache_path = self._get_cache_path(key)
        try:
            df.to_json(cache_path, orient='records', force_ascii=False)
            print(f"  ✓ 已保存到缓存（{key}）")
        except Exception as e:
            print(f"  ✗ 缓存保存失败: {e}")


# 创建全局缓存实例
cache = DataCache()


def get_realtime_with_cache(use_cache=True, cache_timeout=5):
    """
    获取实时行情（带缓存）
    
    参数:
        use_cache: 是否使用缓存
        cache_timeout: 缓存超时时间（分钟）
    """
    cache_key = "realtime_quotes"
    
    # 尝试读取缓存
    if use_cache:
        cached_data = cache.get(cache_key, max_age_minutes=cache_timeout)
        if cached_data is not None:
            return cached_data
    
    # 缓存未命中，请求数据
    df = get_realtime_quotes_safe()
    
    # 保存到缓存
    if df is not None:
        cache.set(cache_key, df)
    
    return df


# ================================================================================
# 方案7：限流保护（全局速率限制）
# ================================================================================

class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self.last_call_time = 0
    
    def wait(self):
        """等待直到可以下一次调用"""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_call_time = time.time()


# 创建全局限流器
rate_limiter = RateLimiter(min_interval=1.5)  # 最少间隔1.5秒


def api_call_with_rate_limit(func, *args, **kwargs):
    """带速率限制的API调用"""
    rate_limiter.wait()
    return func(*args, **kwargs)


# ================================================================================
# 测试运行
# ================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("AKShare 网络问题解决方案测试")
    print("=" * 80)
    
    # 测试1：获取历史数据（带重试）
    print("\n【测试1】获取历史数据（带重试机制）")
    df_history = get_stock_history_safe("000001", days=30)
    if df_history is not None:
        print(df_history.head())
    
    # 测试2：获取实时行情（带重试）
    print("\n【测试2】获取实时行情（带重试机制）")
    df_realtime = get_realtime_quotes_safe()
    if df_realtime is not None:
        print(df_realtime[['代码', '名称', '最新价', '涨跌幅']].head())
    
    # 测试3：获取实时行情（带缓存）
    print("\n【测试3】获取实时行情（带缓存）")
    df_cached = get_realtime_with_cache(use_cache=True)
    if df_cached is not None:
        print(f"数据条数: {len(df_cached)}")
    
    # 测试4：再次获取（应该命中缓存）
    print("\n【测试4】再次获取（应该命中缓存）")
    df_cached2 = get_realtime_with_cache(use_cache=True)
    if df_cached2 is not None:
        print(f"数据条数: {len(df_cached2)}")
    
    # 测试5：备用数据源
    print("\n【测试5】备用数据源（新浪财经）")
    df_backup = get_realtime_backup()
    if df_backup is not None:
        print(df_backup[['代码', '名称', '最新价', '涨跌幅']].head())
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
