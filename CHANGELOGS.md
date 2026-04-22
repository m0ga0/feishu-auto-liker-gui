# 更新日志

## 2026-04-11

### 优化

- **修复重复点赞问题**: 添加 `reacted_ids` 持久化状态，避免重启监控后重复点赞已处理消息
  - 新增 `mark_reacted()` / `is_reacted()` 方法
  - 修改 `_save_state()` 保存 `reacted_ids` 到 state.json
  - 修改监控循环，点赞前检查 `is_reacted()`

- **修复工具栏定位问题**: 使用 JavaScript 定位消息对应的点赞按钮
  - `_react()` 方法改为通过 `evaluate_handle()` 查找距消息中心最近的点赞按钮
  - 移除 page-level fallback，避免所有点赞点到同一个按钮

- **移除重复消息处理**: 改用 `seen_ids` 追踪已处理消息
  - `_get_messages()` 和 `_run_loop()` 都检查 `is_seen()`
  - 避免同一消息被重复处理

- **移除不必要的延迟**
  - `_react()` 中移除 hover 后延迟
  - 点击后移除延迟
  - 加快点赞速度

- **修复状态重置问题**: 停止监控后再启动时恢复已点赞状态
  - `reset()` 方法不再删除 state.json 和清空 `_group_states`
  - 只重置计数器

### 代码修复

- 修复 `_react()` 方法缩进问题
- 移除死代码（重复的 try-except 块）
- 修复 `evaluate_handle` 参数传递（使用 `message_element` 作为参数）
