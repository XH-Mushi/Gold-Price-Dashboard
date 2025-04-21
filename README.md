# 全球市场数据分析仪表板

这是一个使用 Streamlit 构建的数据分析仪表板，集成了销售数据分析和全球黄金价格分析功能。

## 功能特点

### 销售数据分析

- 销售额、访问量和转化率的实时监控
- 交互式销售趋势图表
- 访问量与转化率关系分析
- 原始数据查看和筛选

### 黄金价格分析

- 实时全球黄金价格数据（美元/盎司 与 人民币/克）
- 国内外金价对比与溢价分析
- 价格趋势和波动性分析
- 技术指标分析（如 RSI）
- 季节性分解分析
- 价格相关性分析
- 数据缓存和历史记录

## 最新更新

- **2025-4-20**:
  - 修复了数据点不足导致的索引错误问题
  - 增强了错误处理机制，提高了应用稳定性
  - 改进了图表绘制函数，使其能够优雅处理空数据
  - 添加了用户友好的错误提示，指导用户如何解决数据不足问题

## 安装说明

1. 克隆项目到本地：

```bash
git clone [repository-url]
cd dashboard_demo
```

2. 创建并激活 conda 环境：

```bash
conda create --prefix ./env python=3.10
conda activate ./env
```

3. 安装依赖包：

```bash
pip install -r requirements.txt
```

## 运行方式

在项目目录下运行：

```bash
streamlit run app.py
```

## 本地访问方式

启动应用后，可通过以下 URL 访问：

- 本地 URL: http://localhost:8507
- 网络 URL: http://[your-ip]:8507

## 技术栈

- Python 3.10
- Streamlit 1.32.0
- Pandas 2.2.0
- Plotly 5.18.0
- NumPy 1.26.0
- yfinance (用于获取黄金价格数据)
- statsmodels (用于趋势分析)
- SQLite (用于数据存储)

## 错误处理

应用内置了多重错误处理机制：

- 网络请求失败自动重试
- 数据源不可用时自动尝试备用数据源
- 数据点不足时提供友好提示
- 图表生成失败时显示错误信息而不是崩溃

## 数据来源

- 销售数据：示例数据（随机生成）
- 黄金价格数据：Yahoo Finance API

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License
