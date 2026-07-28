# Q1 全章执行与输出刷新 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 跑通 Q1 notebook 全章（Step 1 到 Step 7），并将当前固定最近 5 年窗口下的真实输出刷新回 notebook。

**Architecture:** 继续使用现有的 `q1-strategy.ipynb` 作为唯一教学产物，不拆分代码模块。先补齐执行 notebook 所需的本地依赖，再用受控脚本顺序执行 notebook 各代码单元，最后把新的 stdout / 图表输出写回 ipynb JSON。

**Tech Stack:** Python 3.12、pandas、numpy、matplotlib、yfinance、notebook JSON（nbformat 兼容结构）

## Global Constraints

- 数据窗口固定为 `2021-07-28` 到 `2026-07-27`
- notebook 路径必须保持为 `docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb`
- README 路径必须保持为 `docs/superpowers/specs/course/q1-how-to-profit/README.md`
- 不得回退为动态 `today` / `now()` 数据窗口
- 下载为空时必须抛出明确错误并停止执行

---

### Task 1: 准备 notebook 执行环境

**Files:**
- Modify: `docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb`
- Test: `tests/notebooks/test_q1_notebook.py`

**Interfaces:**
- Consumes: 当前 notebook 代码单元、`.venv` Python 环境
- Produces: 可执行 notebook 运行环境；已通过的结构回归测试

- [ ] **Step 1: 运行 notebook 结构测试，确认基线**

Run: `.venv/bin/pytest tests/notebooks/test_q1_notebook.py -q`
Expected: PASS

- [ ] **Step 2: 检查 `.venv` 中 notebook 执行所需依赖**

Run: `.venv/bin/python - <<'PY'
import importlib.util
mods=['pandas','numpy','matplotlib','yfinance']
for m in mods:
    print(m, bool(importlib.util.find_spec(m)))
PY`
Expected: 四项均为 `True`

- [ ] **Step 3: 如缺失依赖则补齐最小执行集**

Run: `.venv/bin/pip install yfinance matplotlib`
Expected: 安装成功且无错误退出

- [ ] **Step 4: 再次运行结构测试确认未回退**

Run: `.venv/bin/pytest tests/notebooks/test_q1_notebook.py -q`
Expected: PASS

### Task 2: 执行 Q1 全章并刷新 notebook 输出

**Files:**
- Modify: `docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb`
- Test: `tests/notebooks/test_q1_notebook.py`

**Interfaces:**
- Consumes: `q1-strategy.ipynb` 代码单元顺序、510300.SS 在线数据
- Produces: 已刷新输出的 notebook；Step 1 到 Step 7 的真实执行结果

- [ ] **Step 1: 写执行脚本，按顺序跑 notebook 代码单元并捕获输出**

```python
import io
import json
import base64
from contextlib import redirect_stdout
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

nb_path = Path("docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
env = {}

for cell in nb["cells"]:
    if cell.get("cell_type") != "code":
        continue
    stdout_buffer = io.StringIO()
    with redirect_stdout(stdout_buffer):
        exec("".join(cell["source"]), env)
    cell["outputs"] = []
    text = stdout_buffer.getvalue()
    if text:
        cell["outputs"].append({
            "name": "stdout",
            "output_type": "stream",
            "text": text.splitlines(True),
        })
    figures = [plt.figure(num) for num in plt.get_fignums()]
    for fig in figures:
        img = io.BytesIO()
        fig.savefig(img, format="png", bbox_inches="tight")
        cell["outputs"].append({
            "output_type": "display_data",
            "data": {
                "image/png": base64.b64encode(img.getvalue()).decode("ascii"),
                "text/plain": ["<Figure refreshed by Codex>"],
            },
            "metadata": {},
        })
        plt.close(fig)
```

- [ ] **Step 2: 运行执行脚本并覆盖写回 notebook**

Run: `MPLCONFIGDIR=/private/tmp/mplconfig .venv/bin/python <script>`
Expected: 成功执行全部代码单元；ipynb 被刷新

- [ ] **Step 3: 单独打印 Step 1 / Step 2 / Step 5 / Step 6 / Step 7 关键结果做人工核对**

Run: `MPLCONFIGDIR=/private/tmp/mplconfig .venv/bin/python - <<'PY'
import yfinance as yf
import pandas as pd
import numpy as np

DATA_START = "2021-07-28"
DATA_END = "2026-07-27"
download_end = (pd.Timestamp(DATA_END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
df = yf.download("510300.SS", start=DATA_START, end=download_end, auto_adjust=True, multi_level_index=False, progress=False)
df = df.loc[:DATA_END]
assert not df.empty

def backtest_dca(df, monthly_amount=1000):
    df = df.copy()
    df["month"] = df.index.to_period("M")
    monthly_first = df.groupby("month").first()
    shares_bought = monthly_amount / monthly_first["Close"]
    total_shares = shares_bought.cumsum()
    total_cost = monthly_amount * np.arange(1, len(monthly_first) + 1)
    monthly_last = df.groupby("month").last()
    portfolio_value = total_shares * monthly_last["Close"]
    returns = (portfolio_value.values - total_cost) / total_cost
    return pd.DataFrame({"total_cost": total_cost, "total_shares": total_shares.values, "portfolio_value": portfolio_value.values, "return": returns}, index=monthly_first.index)

def backtest_dca_with_ma(df, monthly_amount=1000, ma_period=20):
    df = df.copy()
    df["ma"] = df["Close"].rolling(ma_period).mean()
    df["month"] = df.index.to_period("M")
    monthly_first = df.groupby("month").first()
    monthly_first["signal"] = monthly_first["Close"] > monthly_first["ma"]
    shares_list, cost_list = [], []
    total_shares, total_cost = 0, 0
    for _, row in monthly_first.iterrows():
        if pd.notna(row["ma"]) and row["signal"]:
            total_shares += monthly_amount / row["Close"]
            total_cost += monthly_amount
        shares_list.append(total_shares)
        cost_list.append(total_cost)
    monthly_last = df.groupby("month").last()
    portfolio_value = np.array(shares_list) * monthly_last["Close"].values
    cost_array = np.array(cost_list)
    returns = np.zeros(len(cost_array))
    mask = cost_array > 0
    returns[mask] = (portfolio_value[mask] - cost_array[mask]) / cost_array[mask]
    return pd.DataFrame({"total_cost": cost_list, "total_shares": shares_list, "portfolio_value": portfolio_value, "return": returns, "signal": monthly_first["signal"].values}, index=monthly_first.index)

result_dca = backtest_dca(df)
scan_df = pd.DataFrame([{"ma_period": ma, "return": backtest_dca_with_ma(df, ma_period=ma)["return"].iloc[-1]} for ma in range(5, 121, 5)])
split_idx = int(len(df) * 0.6)
train = df.iloc[:split_idx]
test = df.iloc[split_idx:]
print("data_range", df.index[0].date(), df.index[-1].date(), len(df))
print("dca_final", float(result_dca["return"].iloc[-1]))
print("scan_best", int(scan_df.loc[scan_df["return"].idxmax(), "ma_period"]), float(scan_df["return"].max()))
print("train_test", len(train), len(test), train.index[0].date(), train.index[-1].date(), test.index[0].date(), test.index[-1].date())
PY`
Expected: 输出关键指标且无异常

- [ ] **Step 4: 重新运行 notebook 结构测试**

Run: `.venv/bin/pytest tests/notebooks/test_q1_notebook.py -q`
Expected: PASS

### Task 3: 汇总评估与后续建议

**Files:**
- Modify: none
- Test: none

**Interfaces:**
- Consumes: Task 2 的执行结果
- Produces: 面向用户的 Q1 有效性评估与下一步建议

- [ ] **Step 1: 汇总第一个策略与全章关键指标**

记录：
- Step 1 数据范围与总行数
- Step 2 定投最终收益率
- Step 6 最优均线参数与收益
- Step 7 样本外测试结论

- [ ] **Step 2: 对 notebook 有效性给出简洁评估**

输出应覆盖：
- 教学链是否完整
- 当前是否仍依赖网络
- 是否建议加入本地缓存或快照
- 是否建议继续进入模拟验证阶段

- [ ] **Step 3: 报告结果并等待下一步指令**

报告中必须包含：
- notebook 已刷新输出
- 测试结果
- 当前未解决的问题（如仍存在 warning 或网络依赖）
