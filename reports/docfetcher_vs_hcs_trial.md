# DocFetcher 与 HCS 混合检索：三题双流程对照

> 范围：只做 3 个已见任务的流程对照。DocFetcher 使用 1.1.27 固定便携版；HCS 使用现有 `hybrid_top5`，**自动补证关闭**。不安装新工具，不改模型、参数或 gold。  
> 操作由 AI 代理完成；不计算真人节省时间，不宣称独立测试或产品胜出。

## 1. 资料与解析条件

| 项 | DocFetcher | HCS |
|---|---|---|
| 资料 | 独立目录中仅 A、B 两份锁定 PDF | 锁定版 A/B 条款语料 |
| 正文来源 | PDF 文本层 | A：交通运输部 HTML；B：市场监管总局 HTML（PDF 仅作页锚点） |
| 解析是否相同 | **不同** | **不同** |

因此不能宣称两边解析条件完全相同。HCS 的 `corpus/docs_manifest.json` 记录 A 正文来自 HTML、B 正文来自 HTML；DocFetcher 索引的是 PDF。

对 HCS 返回的条款做了 HTML 全文与 PDF 页文本的按句核对（`reports/docfetcher_vs_hcs_trial_parse_check.json`）：

- A8：PDF 第2页可找到主体文字，分句覆盖约 0.5；A8 跨段落/页边断行，机器覆盖不能当作逐字一致。
- A16：PDF 第4页，分句覆盖约 0.75；HCS 本地回跳和 PDF 页面均实际打开确认。
- A61：PDF 第18/19页，分句覆盖 1.0；HCS 本地回跳和 PDF 页面均实际打开确认。
- B49：PDF 第11页，覆盖约 0.5；B48 未匹配 PDF 页；B58 第13页覆盖约 0.25；B16 第4页覆盖约 0.286。
- B50、B59、B29、B30、A50、A55 等返回条款在 PDF 页文本中覆盖为 1.0。

结论：A8/A16/A61 的充分依据已实际打开确认；部分 B 侧命中条款在 PDF 文本层不能完整对齐，**没有把它们当作充分依据**。两边正文内容总体相邻，但不能声称解析条件相同或逐字一致。

## 2. DocFetcher 预览功能实际尝试

在 Q1 结果 A_spec 上，DocFetcher 预览加载 PDF 第1页。实际检查预览工具栏 5 个按钮：

- 按钮 0、1：`enabled=False`（上一/下一命中不可用）。
- 按钮 2、3、4：`enabled=True`；逐个点击后，预览可见文字、页码/页面内容与黄色像素均未变化（截图 `12_df_preview_page1.png`、`13_df_nav_btn3_nochange.png`）。
- 没有找到能把预览滚到 A8/A16/A61 的其他可见翻页控件。

因此本轮预览只能确认“加载第1页并显示黄色高亮”；**没有因第一次停在第一页就直接判定无法定位**，而是继续打开原 PDF，用 Edge 查找定位。这个限制保留，不把预览命中当作答案展示。

## 3. HCS 实际返回（hybrid_top5，补证关闭）

真实逐条结果、展示文字、出处和相对回跳链接见 `reports/docfetcher_vs_hcs_trial_hcs.json`。

| 查询 | 决策 | 前5条顺序 | 充分依据 |
|---|---|---|---|
| Q1 完整问题 | answer | A8 → B50 → B48 → B29 → B30 | A8（第1位） |
| Q1 关键词 | answer | A8 → B48 → A55 → B30 → A50 | A8（第1位） |
| Q2 完整问题 | answer | A61 → B49 → A16 → B59 → B58 | A61（第1位）、A16（第3位） |
| Q2 关键词 | answer | A61 → B49 → A16 → B58 → B16 | A61、A16 |
| Q3 完整问题 | refuse | 无返回 | **无充分依据** |
| Q3 关键词 | refuse | 无返回 | **无充分依据** |

HCS 实际回跳已打开：

- A8：`../locators/rail_quality.locator.html#art-8`，Edge 打开后定位到 A8，显示“质量管理机构、专职质量管理人员、监督检查并制作留存检查记录”。截图 `14_hcs_A8_locator.png`。
- A16：`../locators/rail_quality.locator.html#art-16`，定位到竣工验收后15日内备案。截图 `15_hcs_A16_locator.png`。
- A61：`../locators/rail_quality.locator.html#art-61`，定位到逾期30天/超过30天的罚款档次。截图 `16_hcs_A61_locator.png`。

## 4. 逐题对照

| 题 | DocFetcher 实际结果 | HCS 实际结果 | 充分依据与不足 | 哪边更直接 |
|---|---|---|---|---|
| Q1 质量管理人员/检查记录 | 6 次查询均命中 A/B 两个文件；预览第1页；A8 需打开原 PDF 查找 | A8 第1位；另返回 B50/B48/B29/B30 等相关条款 | 两边都找到 A8；DocFetcher 的预览未定位，需 Edge；HCS A8 在第1位且有原文回跳 | **HCS 更直接**（排序+展示+回跳）；DocFetcher 需文件级→打开原文 |
| Q2 竣工验收备案/逾期罚则 | 命中 A/B 两个文件；预览第1页；A16/A61 需打开原 PDF 查找 | A61 第1位、A16 第3位；B49 也返回 | 两边都找到 A16+A61；HCS 直接给出顺序与出处；DocFetcher 需 Edge 查找 | **HCS 更直接**；DocFetcher 可完成但多一步原文定位 |
| Q3 环保验收监测因子/频次 | 命中 A/B 两个文件，但只是相关材料；Edge 查找“监测因子”“频次”均 0/0 | 两轮均为 `refuse`，无返回 | **两边都没有充分依据**；DocFetcher 返回相关文件不是工具错误，把它当答案才是误判；HCS 拒绝更明确 | **持平/尚无法判断**；不能因为 HCS 拒绝就宣称效果胜出 |

## 5. 完整操作轨迹

1. DocFetcher：官方 1.1.27 便携版，独立目录只放 A/B PDF；中文索引 `hcstest` 建立；完整问题与关键词各 3 次查询。
2. DocFetcher Q1：选择 A_spec 结果；预览加载第1页；检查工具栏“上一/下一命中”为禁用；“翻页类”按钮点击无可见变化；未在预览中定位到 A8。
3. DocFetcher：双击结果打开 A_spec；Edge 查找“检查记录”定位 A8 第2页；查找“15日内”定位 A16 第4页；查找“逾期30天”定位 A61 第18页。
4. DocFetcher Q3：A/B 均被命中；Edge 查找“监测因子”“频次”均 0/0；没有把相关材料当答案。
5. HCS：原有 `TaskBSystem.answer(question, "hybrid_top5")`，自动补证关闭；仅传入自然语言问题和方式；没有把 gold 条号/页码/关键词注入查询。
6. HCS 回跳：实际打开 A8/A16/A61 的本地 locator 链接，截图确认锚点与正文；真实 top5 顺序、展示文字、来源写入 JSON。

## 6. 查找词来源

- “检查记录”：来自 Q1 题目。
- “15日内”“逾期30天”：不是查询前使用；先在 DocFetcher 打开 A16/A61 页面读到该文字，再在 PDF 查找中使用，来源步骤为 Q2 打开原文件之后。
- “监测因子”“频次”：来自 Q3 题目。
- HCS 查询只使用原题和预定关键词；没有使用 gold 条号/页码。

## 7. 完成情况与边界

- DocFetcher：中文索引、搜索完成；预览只完成“加载第1页+高亮”，未完成目标条款自动定位；打开原文件并定位完成。
- HCS：真实 top5、顺序、展示文字、出处、locator 链接均已保存；A8/A16/A61 实际打开验证完成；Q3 正确拒绝。
- 本报告只比较流程直接性：Q1/Q2 HCS 更直接，Q3 持平/尚无法判断。不做真人耗时、不宣称独立测试或产品胜出。
- 关键截图目录：`reports/docfetcher_baseline_screens/`；机器记录：`reports/docfetcher_vs_hcs_trial_hcs.json`、`reports/docfetcher_vs_hcs_trial_parse_check.json`。