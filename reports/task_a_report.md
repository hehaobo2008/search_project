# 任务A 自动校验报告

- run_id：taskA-20261102T222831
- 生成时间：2026-11-02T22:28:31.809857+08:00
- 范围：任务A：中文条款切分、原文定位、引用四分法与版本/故障校验
- 自动用例：16，通过：16，失败：0，已更正记录：1
- 人工核验待办：8 项
- 闸门：NOT_PASSED_PENDING_HUMAN_REVIEW

| 用例 | 名称 | 状态 | 证据 |
|---|---|---|---|
| T01 | 文档身份与共页分离 | PASS | documents=3 distinct_source_files=2 shared_page=True |
| T02 | A/B 条号连续且边界完整 | PASS | A=1..75(75条) B=1..82(82条) |
| T03 | 原文偏移回跳与哈希 | PASS | span_fail=0 hash_fail=0 pdf_page_missing=0 |
| T04 | A第2条范围条款 | PASS | ok pdf_page=1 |
| T05 | A第30条检测/取样/签认 | PASS | status=ok keywords=['试块', '监督', '专人签字', '签认'] paras=2 pdf_page=9 |
| T06 | A66→B65 显式条款引用与正确版本 | PASS | status=ok edges=1 target=第六十五条 version=revised_2019_04_23 |
| T07 | B29/B31/B65 原文与页锚点 | PASS | B29 p7 B31 p7 B65 p16 |
| T07b | B31按实际PDF第7页更正并保留旧记录 | PASS | page=7 cross=False legacy=superseded correction=corrected |
| T08 | C修改与重新公布关系 | PASS | amendment=3 targets=['None', '第七十条', '第六十九条'] C_articles=0 |
| T09 | 负例：A30与B29/B31仅主题相关 | PASS | explicit_edges=0 topic_edges=2 |
| T10 | 负例：A1→B 仅文件级不生成条款边 | PASS | A1文件级B边=1 A1条款级边=0 |
| T11 | 显式关系目标无悬空边 | PASS | dangling=0 [] |
| T12 | 版本守卫：2017副本不得静默替代2019 | PASS | status=version_pending available=['revised_2017_10_07'] |
| T13 | 故障用例：缺条/重复/缺版本/错位 | PASS | missing=article_not_found duplicate=ambiguous_article no_version=version_unknown tampered=locator_mismatch |
| T14 | 主题相关与显式引用隔离 | PASS | topic_related=2 |
| T15 | C与A共页去重 | PASS | C_indexed_articles=0 C_edges=3 |

## 人工核验待办（不计入自动通过）

- [ ] H01 A第2条与交通运输部规范PDF物理第1页的视觉一致性
- [ ] H02 A第30条与规范PDF物理第9页的视觉一致性（两款完整、签字主体与签认对象不混同）
- [ ] H03 A第66条与规范PDF物理第22页的视觉一致性（显式引用措辞）
- [ ] H04 B第29条与中科院副本PDF物理第7页的视觉一致性
- [ ] H05 B第31条位置：自动文本层仅第7页，清单记录为续至第8页，冲突待视觉确认
- [ ] H06 B第65条与中科院副本PDF物理第16页的视觉一致性
- [ ] H07 C修改决定全文：修改第69条、增设第70条、条文序号调整与重新公布
- [ ] H08 引用四分法语义复核：A1→B文件级、A30与B29/B31主题相关、A66→B65显式、C→A修改

> 结论：自动链路通过不等于闸门通过；H01-H06 完成并由人工签字后，任务A才可判定通过。
