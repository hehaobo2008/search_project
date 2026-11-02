# 数据来源、版本与哈希校验

本仓库**不包含**法规原文、PDF/HTML 原文件、模型权重或缓存。复现时请从下列官方入口获取，并用 SHA-256 核对；hash 不一致说明来源可能已更新，**不得静默替换锁定版本**。

## 法规材料（A/B/C）

| 角色 | 文件 | 锁定版本 | 官方来源 | SHA-256 |
|---|---|---|---|---|
| rail_quality | `work/raw/A_amend.html` | amended_2021_12_23 | https://xxgk.mot.gov.cn/2020/jigou/fgs/202202/t20220225_3643089.html | `77cbec8ef757d87df1086780d38878afdeb2f1e150b7855276401e25b5bbba16` |
| rail_quality（PDF回跳副本） | `work/raw/A_spec.pdf` | amended_2021_12_23 | https://xxgk.mot.gov.cn/gz/202201/W020220110598772795306.pdf | `4a815f2cecd083c229e6a53ae145595b7c59583aa09371c14703d47adec09b98` |
| construction_quality | `work/raw/B_official.html` | revised_2019_04_23 | https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_e42ecef60e9146af83cf9846821fac6c.html | `96ba6df3b56e1c213035ea94ae9a172af1a23b3b4bed37c9d4a1fd2720e14f9e` |
| construction_quality（PDF回跳副本） | `work/raw/B_copy_cas.pdf` | revised_2019_04_23 | https://ic.cas.cn/yqjj/zcfg/202309/P020230908644966677848.pdf | `651fa2536cc3c86f476324629a4ce4b5ded9479728468622c1831eec8ccb6cb7` |

## 版本反例（仅对照，不进入主索引）

| 文档 | 文件 | 版本 | 来源 | SHA-256 |
|---|---|---|---|---|
| rail_quality | `work/raw/A_2015_old.html` | published_2015_03_12 | https://xxgk.mot.gov.cn/jigou/fgs/202006/t20200623_3307691.html | `a06c8dde9008517bb8ab509405cb2724a1f8e2e621a68a0ba830b44a19a40e83` |
| construction_quality | `work/raw/B_2017_moj.pdf` | revised_2017_10_07 | https://xzfg.moj.gov.cn/law/download?LawID=1598&type=pdf | `93526bed6aadee4609c463080d1c7daf87f455df6ea4cc058a1abbe617f51cc2` |

## 中文检索模型

| 文件 | 来源 | SHA-256 |
|---|---|---|
| `README.md` | ModelScope `Xenova/bge-small-zh-v1.5` | `cb22054df1a98f7ee9d5b281d023e67c27cc316e1733baf03fc994d95c3048ab` |
| `config.json` | ModelScope `Xenova/bge-small-zh-v1.5` | `d4193ead3a810fd694fa8a31d7fc72fbaebc0668b603e398734bf2f6538ff42f` |
| `special_tokens_map.json` | ModelScope `Xenova/bge-small-zh-v1.5` | `b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3` |
| `tokenizer.json` | ModelScope `Xenova/bge-small-zh-v1.5` | `48cea5d44424912a6fd1ea647bf4fe50b55ab8b1e5879c3275f80e339e8fae26` |
| `tokenizer_config.json` | ModelScope `Xenova/bge-small-zh-v1.5` | `e6f3b96db926a37d4039995fbf5ad17de158dfb8f6343d607e4dbaad18d75f5a` |
| `vocab.txt` | ModelScope `Xenova/bge-small-zh-v1.5` | `45bbac6b341c319adc98a532532882e91a9cefc0329aa57bac9ae761c27b291c` |
| `onnx/model.onnx` | ModelScope `Xenova/bge-small-zh-v1.5` | `69a0b846f4f116b5e6aabf9546ea6754d02264f3211a13a1bd69b31b8040749a` |

- 上游模型卡：https://huggingface.co/BAAI/bge-small-zh-v1.5
- 分发仓库：https://www.modelscope.cn/models/Xenova/bge-small-zh-v1.5
- 许可：MIT（ModelScope 模型 API License=mit；BAAI 模型卡为 MIT；Xenova ONNX 转换仓库无独立 LICENSE 文件）
- 运行时：onnxruntime 1.31.0 CPUExecutionProvider；pooling：CLS token of last_hidden_state + L2 normalization；max_length：512

## 下载与校验

```bash
# 法规材料（默认不下载模型）
python scripts/fetch_sources.py

# 连同模型权重（约95MB）
python scripts/fetch_sources.py --model
```

脚本会把文件放入 `work/raw/` 与 `work/models/bge-small-zh-v1.5/`，并逐文件比较 SHA-256。`work/` 已被 `.gitignore` 排除。

## 再分发边界

- 公开可访问不等于已核查再分发许可；本仓库只提供来源与 hash，不随仓库分发法规全文。
- 模型权重不随仓库分发；使用前核对许可与文件 hash。
- 报告中的条款摘录仅用于说明定位与引用关系，具体事项仍须由专业人员核对版本、对象范围及其他必要依据。

