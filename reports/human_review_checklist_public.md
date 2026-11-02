# 任务A 人工核对清单（公开版）

> 本仓库不随附法规原文。请先运行 `python scripts/fetch_sources.py` 获取原文并核对 SHA-256；
> 再按条号、偏移与 PDF 物理页打开原件完成 H01-H08 视觉核对。


本清单列出必须由人工打开原件视觉确认的项目。自动文本层匹配、偏移切片、哈希校验与本地锚点回跳已经通过，但**不能替代视觉核对**。

- 语料生成时间：2026-11-02T22:28:30.810404+08:00
- 偏移约定：正文块按DOM顺序取p/h2/h3/h4；块内连续Unicode空白折叠为单个半角空格并去首尾；块间以单个换行符连接；不做繁简、大小写或标点转换。偏移单位为Python字符串Unicode码点，区间左闭右开，基于各文档独立full_text。
- 本地回跳：点击 `../locators/...#art-N` 在浏览器打开本地定位副本并跳到对应条款；链接为相对路径，复制目录后仍可用；锚点由 `scripts/build_locators.py` 注入，条文文字未改动。
- PDF回跳：`../work/raw/...pdf#page=N` 为物理页跳转，页位来自PDF文本层自动匹配，仍须人工视觉确认。
- 核对结果栏由人工填写；未填写即视为闸门未通过。

## H01 第二条（适用范围）

- 文档：铁路建设工程质量监督管理规定 / rail_quality
- 版本：amended_2021_12_23
- 来源：https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html
- HTML锚点：`art-2`
- 字符偏移：[184, 224)
- 本地回跳：../locators/rail_quality.locator.html#art-2
- PDF回跳：../work/raw/A_spec.pdf#page=1
- PDF：`work/raw/A_spec.pdf` 物理第1页（自动文本层匹配，共25页）
- 原文SHA-256：`a003299dd53a66da2a2f9a4bc18cb7f1ad19f1ac8cc3b40913c6764e5c8f4312`
- 文件SHA-256：`77cbec8ef757d87df1086780d38878afdeb2f1e150b7855276401e25b5bbba16`

- 核对要点：确认原文是否完整、页1版面是否为第二条起始。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H02 第三十条（试块送检、监督取样、资料签认）

- 文档：铁路建设工程质量监督管理规定 / rail_quality
- 版本：amended_2021_12_23
- 来源：https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html
- HTML锚点：`art-30`
- 字符偏移：[3262, 3465)
- 本地回跳：../locators/rail_quality.locator.html#art-30
- PDF回跳：../work/raw/A_spec.pdf#page=9
- PDF：`work/raw/A_spec.pdf` 物理第9页（自动文本层匹配，共25页）
- 原文SHA-256：`439bfa857837dfc9c79dd932147a4b698d9e8d0c162fbb11f5b865c7cd7741fb`
- 文件SHA-256：`77cbec8ef757d87df1086780d38878afdeb2f1e150b7855276401e25b5bbba16`

- 核对要点：确认两款完整；签字主体与签认对象不可混同；页9版面与文本层一致。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H03 第六十六条（显式引用B第65条）

- 文档：铁路建设工程质量监督管理规定 / rail_quality
- 版本：amended_2021_12_23
- 来源：https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html
- HTML锚点：`art-66`
- 字符偏移：[8635, 8845)
- 本地回跳：../locators/rail_quality.locator.html#art-66
- PDF回跳：../work/raw/A_spec.pdf#page=22
- PDF：`work/raw/A_spec.pdf` 物理第22页（自动文本层匹配，共25页）
- 原文SHA-256：`3a19e0540004b0bf20b6730ca8c1278522c5160c3a5441d6039ec6e4876aed2c`
- 文件SHA-256：`77cbec8ef757d87df1086780d38878afdeb2f1e150b7855276401e25b5bbba16`

- 核对要点：确认原文写的是‘《建设工程质量管理条例》第六十五条’且位于页22。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H04 第二十九条（检验与专人签字）

- 文档：建设工程质量管理条例 / construction_quality
- 版本：revised_2019_04_23
- 来源：https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_e42ecef60e9146af83cf9846821fac6c.html
- HTML锚点：`art-29`
- 字符偏移：[2656, 2747)
- 本地回跳：../locators/construction_quality.locator.html#art-29
- PDF回跳：../work/raw/B_copy_cas.pdf#page=7
- PDF：`work/raw/B_copy_cas.pdf` 物理第7页（自动文本层匹配，共20页）
- 原文SHA-256：`f8a1492b14b374e30a15f61a75250ba01b99c09e16ca86795fc635d229b87d79`
- 文件SHA-256：`96ba6df3b56e1c213035ea94ae9a172af1a23b3b4bed37c9d4a1fd2720e14f9e`

- 核对要点：确认中科院副本PDF第7页与原网页逐字一致；该副本非原发布机关版本。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H05 第三十一条（监督取样与送检）

- 文档：建设工程质量管理条例 / construction_quality
- 版本：revised_2019_04_23
- 来源：https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_e42ecef60e9146af83cf9846821fac6c.html
- HTML锚点：`art-31`
- 字符偏移：[2830, 2905)
- 本地回跳：../locators/construction_quality.locator.html#art-31
- PDF回跳：../work/raw/B_copy_cas.pdf#page=7
- PDF：`work/raw/B_copy_cas.pdf` 物理第7页（自动文本层匹配，共20页）
- 原文SHA-256：`588c4d40f4a5177598d15e22bb0a179dc41829e5d61db248fa16deb71d265d3e`
- 文件SHA-256：`96ba6df3b56e1c213035ea94ae9a172af1a23b3b4bed37c9d4a1fd2720e14f9e`

- 核对要点：已按实际PDF文本层更正为第7页（旧记录‘续至第8页’保留在docs_manifest的legacy_records中）；请视觉确认第7页页尾与第8页首条。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H06 第六十五条（被引责任条文）

- 文档：建设工程质量管理条例 / construction_quality
- 版本：revised_2019_04_23
- 来源：https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_e42ecef60e9146af83cf9846821fac6c.html
- HTML锚点：`art-65`
- 字符偏移：[6996, 7133)
- 本地回跳：../locators/construction_quality.locator.html#art-65
- PDF回跳：../work/raw/B_copy_cas.pdf#page=16
- PDF：`work/raw/B_copy_cas.pdf` 物理第16页（自动文本层匹配，共20页）
- 原文SHA-256：`1ab1053e8ef659613a34db4e79c6794bdba5055cc0b6297c51b611f8559f6cc8`
- 文件SHA-256：`96ba6df3b56e1c213035ea94ae9a172af1a23b3b4bed37c9d4a1fd2720e14f9e`

- 核对要点：确认第16页原文；本轮只定位，不生成处罚结论。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H07 C修改决定（版本关系）

- 文档：交通运输部关于修改《铁路建设工程质量监督管理规定》的决定 / rail_quality_amendment
- 版本：2021_order_35，公布并施行2021-12-23
- 来源：https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html
- 与A共用文件：`work/raw/A_amend.html`，文件SHA-256：`77cbec8ef757d87df1086780d38878afdeb2f1e150b7855276401e25b5bbba16`
- 本地回跳：../locators/rail_quality_amendment.locator.html#decision

- 自动抽取的修改关系：rail_quality_amendment→第六十九条（将第六十九条修改为）；rail_quality_amendment→第七十条（增加一条，作为第七十条）；rail_quality_amendment→A全文（根据本决定作相应修改并对条文序号作相应调整，重新公布）
- 核对要点：确认修改第69条、增设第70条、条文序号调整后重新公布；C不是第三套检测实体规则。
- 人工结论：☐ 一致　☐ 不一致　☐ 无法打开（原因：__________）
- 核对人：__________　核对时间（含时区）：__________

## H08 引用关系语义复核

- [ ] A第1条对B是**文件级依据引用**，不得展开为B第29、31条。
- [ ] A第30条与B第29、31条只标**主题相关**，不是显式引用。
- [ ] A第66条对B第65条是**条款级显式引用**，目标版本必须是2019年第二次修订版。
- [ ] C对A第69、70条是**修改/重新公布关系**，不是并列实体规则。
- 复核人：__________　复核时间（含时区）：__________

## 闸门判定（人工填写）

- 计划用例总数：自动16 + 版本反例6 + 人工8 = 30
- 自动用例：16 项（通过 16、失败 0、已更正记录 1）
- 版本反例：6 项（通过 6、失败 0）
- 回归测试：26 项，通过 26，跳过测试类 1 个、测试用例 0 个，失败/错误 0
- 人工项：8 项（待核验）
- 闸门结论：☐ 通过　☐ 未通过　☐ 待核验
- 签字：__________　日期：__________

> 只有 H01-H08 全部核对且无关键缺陷时，才可填写“通过”。自动用例与回归测试通过不等同人工复核。