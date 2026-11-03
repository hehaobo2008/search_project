# DocFetcher 1.1.27 流程试跑报告

> 本报告是 DocFetcher 基线的**流程试跑**，不是 HCS 或 DocFetcher 的独立效果测试。  
> 操作由 AI 代理通过 Windows UI Automation/鼠标键盘完成，不把操作耗时写成人类耗时。

## 1. 工具与来源

- 工具：DocFetcher 1.1.27 Windows 64-bit Portable
- 官方下载页：https://docfetcher.sourceforge.io/zh/download/
- 实际下载：SourceForge 官方文件
  `https://master.dl.sourceforge.net/project/docfetcher/docfetcher/1.1.27/DocFetcher-1.1.27-Windows-64bit-Portable.zip`
- ZIP SHA-256：`ae76d2070f15f34838ca4dcd60b48506e503cc58e7310dcd4cbed07f27f2dc96`
- ZIP 大小：122,316,950 bytes；解压 588 项。
- 程序版本：1.1.27 / build 20260119-235832；OpenJDK 21.0.8。
- 未使用第三方改版，未关闭 Windows 安全防护，未安装付费组件。

## 2. 独立测试目录与资料

测试目录：`<TEST_DIR>`（本机使用短路径，以绕过文件夹选择器对长路径的输入限制）。

只复制锁定版 A、B 两份 PDF，没有复制 HTML，也没有把同一文档的 HTML/PDF 重复计入：

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| A_spec.pdf | 304,501 | `4a815f2cecd083c229e6a53ae145595b7c59583aa09371c14703d47adec09b98` |
| B_copy_cas.pdf | 877,965 | `651fa2536cc3c86f476324629a4ce4b5ded9479728468622c1831eec8ccb6cb7` |

## 3. 中文分词与索引

- `conf/settings-conf.txt`：`LuceneAnalyzer = 2`
- 系统语言：`user.language=zh`
- 随包中文分析器：`lib/ansj_seg-5.1.2.jar`、`lib/ansj_lucene6_plug-5.1.2.0.jar`
- 创建的索引名：`hcstest`；索引目录：`indexes/hcstest_1793667951268`
- 索引在未改动分析器配置的情况下建立，随后中文查询返回结果。
- 限制：DocFetcher 1.1.27 的“偏好设置”只有通用选项，没有独立的中文分词开关；因此记录的是启动配置和随包 Ansj 分析器，而不是 UI 勾选项。

实际创建步骤：右键“搜索范围” → “创建索引” → “文件夹...” → 选择 `<TEST_DIR>` → 在索引配置窗口点击“运行”。索引创建后左侧出现 `hcstest`。

期间遇到一次 DocFetcher 自身异常：在空搜索范围上按 Enter 触发 `SimpleTreeViewer` NullPointerException；重启后改用右键菜单完成创建。该异常未被隐藏，也没有用其他检索程序替代。

## 4. 三个任务的完整问题与关键词

每题先输入完整问题，再输入预定关键词；两次结果都保留。

| 任务 | 完整问题 | 预定关键词 |
|---|---|---|
| Q1 | 建设单位需要配备什么质量管理人员、谁留存检查记录？ | 质量管理 检查记录 |
| Q2 | 竣工验收后多久备案，逾期备案罚则在哪？ | 竣工验收 备案 逾期 |
| Q3 | 环保验收需要监测哪些因子、频次多少？ | 环境保护 监测 频次 |

6 次查询均返回 2 个命中文件：`A_spec.pdf`、`B_copy_cas.pdf`。命中文件不等于证据充分，下述结论按打开原文后的条款判断。

### Q1

- 完整问题命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 关键词命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 预览：加载 A_spec 第1页；完整问题/关键词的黄色高亮像素分别为 80/5120（整窗截图的预览区域）。
- 打开原文：从 DocFetcher 双击 A_spec 结果，Edge 打开 `A_spec.pdf`；在 PDF 内查找“检查记录”，定位到第2页 A8。
- A8 原文明确：建设单位应配备专职质量管理人员，对工程质量进行监督检查并制作、留存检查记录。
- 结论：**有充分依据（A8）**。B 命中不代表 B 是本题答案。

### Q2

- 完整问题命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 关键词命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 预览：加载 A_spec 第1页；完整问题/关键词的黄色高亮像素分别为 1355/0。预览没有自动跳到备案条款页。
- 打开原文：Edge 打开 A_spec；查找“15日内”定位到第4页 A16，查找“逾期30天”定位到第18页 A61。
- A16：竣工验收合格之日起15日内，将竣工验收报告、认可文件或准许使用文件送相关部门备案。
- A61：报送备案逾期30天以内处20万至30万元罚款；超过30天处30万至50万元罚款。
- 结论：**有充分依据（A16 + A61）**；两页均从 DocFetcher 结果打开的原 PDF 中定位。

### Q3

- 完整问题命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 关键词命中：A_spec.pdf、B_copy_cas.pdf（结果数 2）
- 预览：加载 A_spec 第1页；完整问题/关键词的黄色高亮像素分别为 0/485。
- 打开原文：A_spec 与 B_copy_cas 均已从 DocFetcher 结果打开；在 Edge 中查找“监测因子”“频次”，均显示 `0/0`。
- A/B 只出现环保、验收、备案等相邻概念，没有监测因子或监测频次规定。
- 结论：**未找到充分依据**。不强行用相邻条款答题。

## 5. 完成情况

| 能力 | 状态 | 证据 |
|---|---|---|
| 中文索引 | 完成 | `hcstest` 索引存在；中文查询有结果 |
| 中文搜索 | 完成 | 6 次查询均返回 A/B 两个文件 |
| 预览与高亮 | 部分完成 | 预览加载 PDF 第1页并显示黄色高亮；未自动跳到 A8/A16/A61 所在页 |
| 打开原文件并定位 | 完成 | A8 第2页、A16 第4页、A61 第18页；Q3 查找 0/0 |

预览的限制必须保留：DocFetcher 的预览没有把命中页自动滚动到目标条款，黄色像素也只说明第1页存在匹配，不代表预览已展示答案。因此 Q1/Q2 的最终定位以 Edge 打开原 PDF 后的查找结果为准；Q3 以此判定没有充分依据。

## 6. 关键截图

目录：`reports/docfetcher_baseline_screens/`

- `01_index_config.png`：索引配置（索引名、路径、文件类型）
- `02_index_created.png`：创建后的 `hcstest` 搜索范围
- `03_q1_full.png`：Q1 完整问题结果
- `04_q1_kw_preview.png`：Q1 关键词结果/预览
- `05_q1_A8_page2.png`：A8 第2页定位
- `06_q2_full.png`：Q2 完整问题结果
- `07b_q2_A16_page4.png`：A16 第4页备案时限
- `07_q2_A61_page18.png`：A61 第18页逾期罚则
- `08_q3_full.png`：Q3 完整问题结果
- `09_q3_A_no_match.png`：A_spec 查找“监测因子” 0/0
- `10_q3_B_no_match.png`：B_copy_cas 查找“频次” 0/0
- `11_q3_kw_preview.png`：Q3 关键词结果/预览

机器可读记录：`reports/docfetcher_baseline_trial_queries.json`。