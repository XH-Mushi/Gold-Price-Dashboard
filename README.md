# 全球市场数据分析仪表板

这是一个使用 Streamlit 构建的数据分析仪表板，集成了销售数据分析和全球黄金价格分析功能。

## 功能特点

### 销售数据分析

- 销售额、访问量和转化率的实时监控
- 交互式销售趋势图表
- 访问量与转化率关系分析
- 原始数据查看和筛选

### 黄金价格分析

- 实时全球黄金价格数据
- 价格趋势和波动性分析
- 交易量分析
- 30 天移动平均价格
- 年度最高价格追踪

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

## 技术栈

- Python 3.10
- Streamlit 1.32.0
- Pandas 2.2.0
- Plotly 5.18.0
- NumPy 1.26.0
- yfinance (用于获取黄金价格数据)
- statsmodels (用于趋势分析)

## 数据来源

- 销售数据：示例数据（随机生成）
- 黄金价格数据：Yahoo Finance API

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License
