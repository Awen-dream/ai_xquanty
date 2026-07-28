# Q1 Notebook 交付设计

## 背景

我们现在已经有一套整理过的课程 specs，位于 `docs/superpowers/specs/course/q1-how-to-profit/specs/`，配套的复盘与评审记录位于 `insights/` 目录。接下来的目标，是把 Q1 这一章真正交付成一份可运行的 notebook 教学产物，同时继续和主线 `ai_xquanty` 包实现保持隔离。

这个交付物应当尽量贴近教学 specs 本身，而不是直接复用包里的回测引擎。它的定位是面向课程学习者的教学材料，而不是对现有工程代码做一层内部封装。

## 目标

在仓库中交付一个独立的 Q1 notebook 工作区，并满足以下目标：

- 与 `ai_xquanty` 包代码清晰隔离；
- 按顺序实现 `q1-how-to-profit` 的 `spec-01..07` 教学链路；
- 可以从上到下完整运行，形成连贯的一章内容；
- 保留课程教学意图，特别是参数扫描与过拟合揭示的渐进式设计。

## 建议的交付形态

直接使用现有课程 spec 目录，并在其中放置一个作为主产物的 notebook：

```text
docs/superpowers/specs/course/
  q1-how-to-profit/
    README.md
    notebooks/
      q1-strategy.ipynb
```

这样做的原因：

- 单个 notebook 最适合当前这条强顺序依赖的 spec 链；
- 可运行产物与 specs 放在一起，可以减少跨目录漂移；
- `README.md` 可以作为一份小型执行约定，而不用把这类说明混到仓库顶层文档；
- 未来 Q2/Q3 章节也可以沿用相同结构扩展。

## 范围边界

### 范围内

- 一份按顺序实现七个教学 spec 的 Q1 notebook；
- 一份本地 readme，说明如何运行 notebook，以及它包含什么；
- 为保证这章内容在当前仓库里可运行而做的轻量 notebook 侧配置。

### 范围外

- 为了支持 notebook 去重构 `ai_xquanty` 包代码；
- 强行要求 notebook 调用包内部函数；
- 把课程 notebook 做成可复用的生产级研究框架；
- 扩展到 Q1 章节以外的内容。

## 实现思路

### 方案 A —— 推荐

在 `docs/superpowers/specs/course/q1-how-to-profit/` 下直接构建一份独立 notebook 实现，并严格按课程 specs 落地。

权衡：

- 优点：
  - 最贴近教学 specs；
  - 避免把课程教学逻辑绑死在包内部实现上；
  - 作为学习产物最容易理解；
  - 从长期看，“课程 demo”和“工程引擎”边界最清楚。
- 缺点：
  - 与包代码会存在一定概念层面的重复；
  - notebook 会刻意保留更简单、更教学化的实现方式。

### 方案 B

仍然做 notebook，但在内部尽可能静默复用 `ai_xquanty` 包函数。

权衡：

- 优点：
  - 减少重复逻辑；
  - 如果工程复用是第一目标，会更快。
- 缺点：
  - 容易偏离课程 specs；
  - 学习者更难直接理解 notebook 在做什么；
  - 课程产物会被工程约束反向绑定。

### 方案 C

把 Q1 拆成多个 notebook，例如每个 spec 一个，或每个小节一个。

权衡：

- 优点：
  - 章节边界更强。
- 缺点：
  - 不适合当前这条强顺序依赖的 spec 链；
  - 重复初始化与状态传递会变得别扭；
  - 不利于一键从头运行整章内容。

### 推荐结论

采用方案 A。

它最符合当前方向：做一个独立可教学、忠于 specs、并与包主线清晰隔离的课程产物。

## Notebook 架构

notebook 应按与 spec 链一致的顺序组织章节：

1. notebook 环境与导入设置
2. 固定时间窗 ETF 数据获取
3. 简单定投回测
4. 与基准对比
5. 均线可视化
6. 均线择时策略
7. 参数扫描
8. 训练集 / 测试集过拟合验证

每一节都应满足：

- 消费前面章节产出的结果；
- 暴露后续 specs 期望的变量 / 函数名，例如 `df`、`result_dca`、`backtest_dca`、`backtest_dca_with_ma`、扫描结果等；
- 可以按从上到下的顺序运行，不依赖 notebook 外部隐藏状态。

## 数据与可复现性规则

为了与收紧后的课程 specs 保持一致：

- 使用 spec 链里固定的数据窗口，而不是“最新可用数据”；
- 保持 notebook 实现自包含；
- 在 revised specs 已要求的关键位置，显式加入校验单元；
- 保留参数扫描与过拟合揭示的教学顺序，而不是“优化掉”这个教学过程。

## 文件职责

### `docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb`

- 主课程产物；
- 包含整章的代码、图表、校验与叙事流程；
- 严格按 spec 顺序展开。

### `docs/superpowers/specs/course/q1-how-to-profit/README.md`

- 说明这份 notebook 是什么；
- 说明如何在本地打开与运行；
- 说明它是一个课程产物，而不是包主线的一部分；
- 把运行说明留在课程目录本地，而不是污染顶层文档。

## 验证策略

这个交付物的成功标准不是“做出一个库级抽象”，而是：

- notebook 存在于选定路径；
- notebook 结构与 spec 顺序一致；
- 后续单元可以依赖前面单元暴露出的变量 / 函数；
- 整章可以从头到尾运行，不需要对包级集成做额外改动；
- 最后几节能清楚展示预期教学弧线，特别是“参数扫描 → 过拟合揭示”。

## 风险与缓解

### 风险 1：不小心与 `ai_xquanty` 绑定过深

缓解方式：

- 保持 notebook 逻辑自包含；
- 除非 spec 明确要求，否则不要导入包里的回测 helper。

### 风险 2：章节间 notebook 状态漂移

缓解方式：

- 保留下游章节依赖的精确变量 / 函数名；
- 在关键章节后加入小型验证单元。

### 风险 3：把课程产物过度工程化

缓解方式：

- 优先追求可读性与 spec 忠实度，而不是复用；
- 除非 notebook 明显难以维护，否则不要额外抽 helper module。

## 执行计划形态

实现计划应把它看作一个顺序推进的 notebook 子项目：

1. 搭建 `docs/superpowers/specs/course/q1-how-to-profit/` 工作区；
2. 创建 notebook 结构与章节骨架；
3. 按顺序实现 spec 链；
4. 增加本地 readme，并做最终验证。

## 审核检查

这份设计默认以下假设成立：

- 整个 Q1 章节使用一个 notebook；
- 可运行 notebook 直接放在 Q1 课程 spec 目录下；
- 不强制复用 `ai_xquanty` 包内部实现；
- 优先交付 notebook-first 的课程产物，而不是 framework-first 的工程抽象。

如果这些假设仍然成立，下一步就是继续把实现计划细化，并逐步完成 notebook 交付。
