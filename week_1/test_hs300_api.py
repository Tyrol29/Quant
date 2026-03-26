"""
测试沪深300成分股接口
"""
import tushare as ts
import pandas as pd

TUSHARE_TOKEN = "877cd5e05fb5edf3115e7a26e16741c4333d07a1216168bde06e781c"

print("初始化 Tushare API...")
pro = ts.pro_api(TUSHARE_TOKEN)

# 测试1: 获取沪深300成分股
print("\n测试1: 获取沪深300成分股 (index_weight)")
try:
    hs300 = pro.index_weight(index_code='399300.SZ', trade_date='20241231')
    print(f"成功! 获取到 {len(hs300)} 条数据")
    print(hs300.head())
except Exception as e:
    print(f"失败: {e}")

# 测试2: 使用不同的指数代码
print("\n测试2: 尝试使用 000300.SH")
try:
    hs300 = pro.index_weight(index_code='000300.SH', trade_date='20241231')
    print(f"成功! 获取到 {len(hs300)} 条数据")
    print(hs300.head())
except Exception as e:
    print(f"失败: {e}")

# 测试3: 获取日线数据
print("\n测试3: 获取单只股票日线数据")
try:
    df = pro.daily(ts_code='000001.SZ', start_date='20250101', end_date='20250131')
    print(f"成功! 获取到 {len(df)} 条数据")
    print(df.head())
except Exception as e:
    print(f"失败: {e}")

# 测试4: 获取股票基本信息
print("\n测试4: 获取股票基本信息 (daily_basic)")
try:
    df = pro.daily_basic(ts_code='000001.SZ', trade_date='20241231')
    print(f"成功! 获取到 {len(df)} 条数据")
    print(df.head())
except Exception as e:
    print(f"失败: {e}")

print("\n测试完成!")
