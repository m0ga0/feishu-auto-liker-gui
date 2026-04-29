# 飞书自动点赞助手 - 消息检测优化规格

## 日期: 2026-04-10

## 目标

修复消息检测的3个核心问题：
1. 消息唯一ID不稳定导致重复检测
2. 每次重启从头检测，浪费算力
3. Hover无法触发工具栏，导致点赞失败

---

## 问题1: 消息唯一ID

### 当前实现
```python
msg_id = f"{hash(text)}_{idx}"
```

**问题**:
- `hash()` 每次运行结果不同（Python随机化）
- `idx` 只是批次内索引，不具备唯一性

### 新实现

尝试从DOM获取原生ID，备选方案用时间戳+内容hash：

```python
async def _get_message_id(element) -> str:
    """提取消息唯一ID，优先使用飞书原生ID"""
    # 1. 尝试 data-message-id
    msg_id = await element.get_attribute('data-message-id')
    if msg_id:
        return msg_id

    # 2. 尝试其他ID属性
    for attr in ['data-id', 'id', 'data-msg-id']:
        msg_id = await element.get_attribute(attr)
        if msg_id:
            return msg_id

    # 3. 备选：用消息创建时间 + 内容hash
    timestamp = await element.get_attribute('data-timestamp') or str(int(time.time()))
    text_hash = hash(text)  # 这个在单次运行内是稳定的
    return f"{timestamp}_{text_hash}"
```

---

## 问题2: 只检测新消息

### 当前实现
```python
recent_wrappers = wrappers[-max_msgs:]
for msg in messages:
    if self.state.is_seen(msg["id"]):
        continue  # 跳过已读
```

**问题**:
- 每次都取最近10条，下一轮又取同样的10条
- "已读"标记是全局的，无法区分不同群
- 重启后 `hash()` 变化，之前标记全失效

### 新实现

**per-group 状态追踪**:
```python
class GroupState:
    """单个群组的检测状态"""
    def __init__(self, group_name: str):
        self.group_name = group_name
        self.seen_message_ids: set[str] = set()       # 本群已检测的消息ID
        self.last_checked_ids: list[str] = []         # 上轮检测到的最新ids
        self.last_check_time: float = time.time()       # 上轮检测时间
```

**只检测新消息的逻辑**:
```python
async def _get_new_messages(self) -> list[dict]:
    """只获取本轮新出现的消息"""
    all_messages = await self._fetch_all_messages()

    # 获取上一轮记录的last_checked_ids
    last_ids = self.state.get_last_checked_ids()

    new_messages = []
    for msg in all_messages:
        # 跳过已知的旧消息
        if msg["id"] in last_ids:
            break  # 因为是按时间倒序，到这里就全是旧的了
        new_messages.append(msg)

    # 更新last_checked_ids
    if new_messages:
        self.state.update_last_checked_ids([m["id"] for m in new_messages])

    return new_messages
```

**持久化**:
```python
# state.json 结构
{
    "groups": {
        "车位群": {
            "seen_ids": ["msg_123", "msg_456"],
            "last_checked_ids": ["msg_789", "msg_790"],
            "last_check_time": 1712345678.9
        }
    }
}
```

---

## 问题3: Hover触发工具栏

### 当前实现
```python
await message_element.hover()
await self._delay(0.8, 1.2)
toolbar = await message_element.wait_for_selector(".messageAction__toolbar", timeout=2000)
```

**问题**:
- Hover事件可能不触发飞书的工具栏渲染
- 工具栏未渲染时，无法找到点赞按钮

### 新实现

**使用dispatchEvent模拟完整鼠标事件**:
```python
async def _react(self, message_element) -> bool:
    try:
        # ���法1: 先尝试hover，等待工具栏渲染
        await message_element.hover()
        await self._delay(0.8, 1.2)

        # 尝试查找工具栏
        toolbar = await message_element.query_selector(".messageAction__toolbar")

        # 方法2: 如果工具栏不可见，用JS直接操作
        if not toolbar:
            # 通过JS查找并检查点赞状态
            is_praised = await message_element.evaluate("""el => {
                const btn = el.querySelector('.toolbar-item.praise');
                return btn?.classList.contains('active')
                    || btn?.querySelector('.icon-praise-full') !== null;
            }""")
            if is_praised:
                return True  # 已点赞

            # 通过JS点击点赞按钮
            await message_element.evaluate("""el => {
                const btn = el.querySelector('.toolbar-item.praise');
                if (btn) btn.click();
            }""")
            return True

        # 方法3: 如果工具栏可见，正常点击
        # ... 原有逻辑

    except Exception as e:
        self.log(f"点赞异常: {e}")
        return False
```

**更可靠的方案 - 模拟真实鼠标事件**:
```python
async def _simulate_real_hover(self, element):
    """模拟真实鼠标移动到元素上"""
    box = await element.bounding_box()
    if not box:
        return False

    center_x = box['x'] + box['width'] / 2
    center_y = box['y'] + box['height'] / 2

    # 完整的鼠标事件序列
    await self._page.mouse.move(center_x, center_y)
    await self._page.dispatch_event('x={}, y={}'.format(center_x, center_y), 'mouseenter')
    await self._page.dispatch_event('x={}, y={}'.format(center_x, center_y), 'mouseover')

    # 等待工具栏渲染
    await self._delay(0.5, 1.0)
```

---

## 改动范围

### 需要修改的文件
- `main.py`

### 需要修改的类/函数

1. **`_BotState` 类** - 添加 per-group 状态支持
2. **`PatternMatcher` 类** - 无变化
3. **`RPABotCore._get_messages()`** - 使用原生ID
4. **`RPABotCore._react()`** - 改进hover和点赞逻辑
5. **`RPABotCore._run_loop()`** - 只检测新消息

### 配置变更
- 无新增配置项

---

## 测试验证

1. 群内连续消息检测不重复
2. 重启后继续检测新消息（不回头检测旧消息）
3. Hover或不 Hover 都能正确点赞
4. 已点赞消息不被重复点赞
