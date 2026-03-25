# 第一周：AKShare 基础学习

## 🎯 学习目标
- 掌握 AKShare 的安装和基本使用
- 学会获取A股历史数据、实时行情
- 学会数据可视化和简单技术指标计算
- 为后续回测和策略开发打下基础

---

## 📦 环境准备

### 1. 安装必要的包

```bash
# 基础包
pip install akshare pandas matplotlib numpy

# 可选：如果图表中文显示有问题，安装中文字体
pip install matplotlib-fonts-cn
```

### 2. 验证安装

```python
import akshare as ak
print(ak.__version__)

# 测试获取数据
df = ak.stock_zh_a_hist(symbol="000001", period="daily", 
                        start_date="20240101", end_date="20241231")
print(df.head())
```

---

## 📂 文件说明

| 文件 | 说明 |
|------|------|
| `01_akshare基础学习.py` | 主要学习文件，包含10个部分的教程 |
| `stock_000001_history.csv` | 运行后生成的示例数据文件 |
| `pingan_stock_chart.png` | 运行后生成的示例图表 |

---

## 🚀 运行方式

### 方式1：命令行运行
```bash
cd "D:\学习\量化投资学习\week_1"
python 01_akshare基础学习.py
```

### 方式2：VS Code运行
1. 打开 VS Code
2. 文件 -> 打开文件夹 -> 选择 `week_1`
3. 打开 `01_akshare基础学习.py`
4. 点击右上角的运行按钮 ▶️

### 方式3：Jupyter Notebook（推荐用于学习）
如果想交互式学习，可以将代码复制到 Jupyter Notebook 中运行

---

## 📋 学习内容概览

### 第一部分：获取A股历史数据
- 使用 `stock_zh_a_hist` 接口
- 理解前复权(qfq)、后复权(hfq)的区别
- 保存数据到CSV

### 第二部分：获取实时行情
- 使用 `stock_zh_a_spot_em` 接口
- 获取全部A股实时数据
- 查找特定股票信息

### 第三部分：获取指数数据
- 沪深300、上证指数等主要指数
- 了解常用指数代码

### 第四部分：获取股票基本信息
- A股全量股票列表
- 股票总数统计

### 第五部分：数据可视化
- 使用 matplotlib 绘制价格走势图
- 添加成交量图表
- 保存图片

### 第六部分：技术指标计算
- 移动平均线 (MA)
- 相对强弱指标 (RSI)

### 第七部分：板块/概念数据
- 获取概念板块列表
- 行业分类数据

### 第八部分：实用工具函数
- 封装常用功能为类
- 获取涨幅榜/跌幅榜
- 获取股票名称

### 第九部分：练习任务
- 5个实践练习，巩固所学知识

### 第十部分：常见问题
- 数据获取失败的解决方法
- 分钟数据、港股、美股的获取方式

---

## 📝 练习任务

### 练习1：获取茅台数据并计算均线
获取贵州茅台(600519)近90天数据，计算5日、10日、30日均线

<details>
<summary>参考答案</summary>

```python
import akshare as ak

symbol = "600519"
df = ak.stock_zh_a_hist(
    symbol=symbol,
    period="daily",
    start_date="20240101",
    end_date="20241231",
    adjust="qfq"
)

# 计算均线
df['MA5'] = df['收盘'].rolling(window=5).mean()
df['MA10'] = df['收盘'].rolling(window=10).mean()
df['MA30'] = df['收盘'].rolling(window=30).mean()

print(df[['日期', '收盘', 'MA5', 'MA10', 'MA30']].tail(20))
```
</details>

### 练习2：绘制上证指数走势图
获取上证指数本月数据，绘制价格走势图

### 练习3：查找今日强势股
查找今日涨幅超过5%的股票

### 练习4：多股票数据保存
选择3只你感兴趣的股票，获取历史数据并保存到CSV

### 练习5：财务数据获取
尝试获取某只股票的财务数据

---

## 📚 常用接口速查表

### 股票数据
| 接口 | 功能 |
|------|------|
| `ak.stock_zh_a_hist()` | A股历史日线数据 |
| `ak.stock_zh_a_spot_em()` | A股实时行情 |
| `ak.stock_zh_a_hist_min_em()` | A股分钟数据 |
| `ak.stock_hk_hist()` | 港股历史数据 |
| `ak.stock_us_hist()` | 美股历史数据 |

### 指数数据
| 接口 | 功能 |
|------|------|
| `ak.index_zh_a_hist()` | A股指数历史数据 |
| `ak.index_stock_cons_weight_csindex()` | 指数成分股 |

### 其他数据
| 接口 | 功能 |
|------|------|
| `ak.stock_board_concept_name_em()` | 概念板块列表 |
| `ak.stock_board_industry_name_ths()` | 行业板块列表 |
| `ak.stock_financial_report_sina()` | 财务报表 |

---

## ⚠️ 注意事项

1. **数据使用限制**
   - 仅供学习研究使用
   - 不构成投资建议

2. **频率限制**
   - 避免过于频繁的调用
   - 建议将数据缓存到本地

3. **数据延迟**
   - 实时数据有分钟级延迟
   - 不适合高频交易

4. **网络问题**
   - 需要稳定的网络连接
   - 某些网络环境可能需要代理

---

## 🔗 参考资源

- [AKShare 官方文档](https://akshare.akfamily.xyz/)
- [AKShare GitHub](https://github.com/akfamily/akshare)
- [pandas 文档](https://pandas.pydata.org/docs/)
- [matplotlib 文档](https://matplotlib.org/stable/contents.html)

---

## 💡 下一步学习

完成本周学习后，建议继续学习：

1. **Backtrader 回测框架**
   - 使用AKShare数据作为输入
   - 编写和回测交易策略

2. **技术指标深入**
   - MACD、KDJ、布林带等
   - talib 库的使用

3. **数据存储优化**
   - SQLite/MySQL 存储历史数据
   - 避免重复下载

---

祝你学习愉快！🎉
