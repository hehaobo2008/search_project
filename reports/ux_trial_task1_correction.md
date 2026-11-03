# 运行 ux-20261103T112954-93ce 记录更正说明

## 原记录（保留，不修改）

- `run.json` / `events.jsonl` 中 `task_ended` 事件：
  - `outcome = "found"`
  - `selected_evidence = ["construction_quality:art-50"]`
- 该文件为页面写入的原始记录，**保持原样**，不做任何改写。

## 更正原因

任务 1 结果列表第 1 位是 `rail_quality:art-8`（《铁路建设工程质量监督管理规定》第八条），
第 2 位是 `construction_quality:art-50`（《建设工程质量管理条例》第五十条）。
操作者实际核对并确认的是 **A8 原文**，`events.jsonl` 中同时存在：

```
original_open_requested  rail_quality:art-8
original_confirmed       rail_quality:art-8
```

结束任务时，自动化代理用屏幕坐标点击结果卡片上的复选框；页面已滚动，坐标命中落到第 2 项，
因此 `selected_evidence` 被记成了 `construction_quality:art-50`。

## 事实认定

- 这是**界面自动化的坐标误点**，不是检索结果错误，也不是操作者判断改变。
- 该次 `selected_evidence` 记录**不可用于评分**；评分应以上述 `original_*` 事件与截图 `reports/ux_trial_screens/04_task1_original_a8.png` 为准，或直接判定本 run 的结束选择无效。
- `duration_ms = 947761`（约 15.8 分钟）包含代理调试页面/重试的时间，**不是真人操作耗时**。

## 改进项（未在本轮实施）

结果卡片的证据勾选需要可在自动化下稳定命中（如键盘可达、或按 `article_id` 定位），
否则坐标点击会把正确的操作记成错误的选择。
