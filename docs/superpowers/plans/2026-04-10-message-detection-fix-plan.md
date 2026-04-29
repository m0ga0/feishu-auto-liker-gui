# 消息检测优化实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复消息检测的3个核心问题：消息ID不稳定、重复检测、Hover点赞失败

**Architecture:** 在 `_BotState` 中添加 per-group 状态追踪；`_get_messages` 使用飞书原生ID；`_run_loop` 只检测新消息；`_react` 使用模拟鼠标事件+JS备选

**Tech Stack:** Python, Playwright (async)

---

### Task 1: 增强 _BotState 添加 per-group 状态支持

**Files:**
- Modify: `main.py:260-336`

**Goal:** 添加 per-group 状态追踪结构，支持按群区分已检测消息

**Steps:**

- [ ] **Step 1: 修改 _BotState 类，添加 groups 状态结构**

在 `_BotState.__init__` 中添加:
```python
# 新增：per-group 状态
self._group_states: dict[str, dict] = {}
```

在 `_BotState` 中添加新方法:
```python
def get_group_state(self, group_name: str) -> dict:
    """获取指定群组的状态，不存在则创建"""
    if group_name not in self._group_states:
        self._group_states[group_name] = {
            "seen_ids": set(),
            "last_checked_ids": [],
            "last_check_time": 0,
        }
    return self._group_states[group_name]

def mark_seen(self, group_name: str, msg_id: str):
    """标记某群的消息为已读"""
    gs = self.get_group_state(group_name)
    gs["seen_ids"].add(msg_id)

def is_seen(self, group_name: str, msg_id: str) -> bool:
    """检查消息是否已读"""
    gs = self.get_group_state(group_name)
    return msg_id in gs["seen_ids"]

def update_last_checked_ids(self, group_name: str, ids: list[str]):
    """更新某群最后检测的ID列表"""
    gs = self.get_group_state(group_name)
    gs["last_checked_ids"] = ids
    gs["last_check_time"] = time.time()

def get_last_checked_ids(self, group_name: str) -> list[str]:
    """获取某群最后检测的ID列表"""
    gs = self.get_group_state(group_name)
    return gs.get("last_checked_ids", [])
```

- [ ] **Step 2: 修改持久化逻辑，保存 group_states**

修改 `_BotState._save_state`:
```python
def _save_state(self):
    try:
        data = {
            "groups": {
                name: {
                    "seen_ids": list(state["seen_ids"]),
                    "last_checked_ids": state["last_checked_ids"],
                    "last_check_time": state["last_check_time"],
                }
                for name, state in self._group_states.items()
            }
        }
        STATE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.warning(f"保存状态文件失败: {e}")
```

- [ ] **Step 3: 修改加载逻辑**

修改 `_BotState._load_state`:
```python
def _load_state(self):
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            groups_data = data.get("groups", {})
            for name, state in groups_data.items():
                self._group_states[name] = {
                    "seen_ids": set(state.get("seen_ids", [])),
                    "last_checked_ids": state.get("last_checked_ids", []),
                    "last_check_time": state.get("last_check_time", 0),
                }
            logger.info(f"已加载 {len(self._group_states)} 个群组的状态")
        except Exception as e:
            logger.warning(f"加载状态文件失败: {e}")
```

---

### Task 2: 重写 _get_messages 使用飞书原生消息ID

**Files:**
- Modify: `main.py:437-473`

**Goal:** 从飞书DOM获取原生消息ID，备选方案用时间戳+内容hash

**Steps:**

- [ ] **Step 1: 修改 _get_messages 返回群名称**

首先修改方法签名，添加 group_name 参数:
```python
async def _get_messages(self, group_name: str = "") -> list[dict]:
```

- [ ] **Step 2: 重写消息ID提取逻辑**

修改消息ID提取部分:
```python
msg_id = await self._extract_message_id(wrapper, text)
```

添加新方法 `_extract_message_id`:
```python
async def _extract_message_id(self, element, text: str) -> str:
    """提取消息唯一ID，优先使用飞书原生ID"""
    import time

    # 1. 尝试 data-message-id
    msg_id = await element.get_attribute('data-message-id')
    if msg_id:
        return msg_id

    # 2. 尝试其他ID属性
    for attr in ['data-id', 'id', 'data-msg-id']:
        msg_id = await element.get_attribute(attr)
        if msg_id:
            return msg_id

    # 3. 尝试从消息元素内部查找ID
    try:
        msg_content = await element.query_selector('[data-message-id]')
        if msg_content:
            msg_id = await msg_content.get_attribute('data-message-id')
            if msg_id:
                return msg_id
    except:
        pass

    # 4. 备选：用时间戳 + 内容hash (单次运行内稳定)
    timestamp = int(time.time() * 1000)
    text_hash = hash(text)  # Python内稳定
    return f"{timestamp}_{text_hash}"
```

- [ ] **Step 3: 返回结构添加 group_name**

返回消息时包含群名称:
```python
messages.append({
    "id": msg_id,
    "text": text,
    "element": wrapper,
    "group": group_name,
})
```

---

### Task 3: 改写 _run_loop 只检测新消息

**Files:**
- Modify: `main.py:519-567`

**Goal:** 只检测新出现的消息，不重复检测

**Steps:**

- [ ] **Step 1: 修改检测逻辑**

找到消息遍历部分，修改为:
```python
for msg in messages:
    if not self._running:
        break
    group_name = msg.get("group", "")

    # 跳过已知的旧消息（用 last_checked_ids 判断）
    last_ids = self.state.get_last_checked_ids(group_name)
    if msg["id"] in last_ids:
        continue

    # 标记为已读
    self.state.mark_seen(group_name, msg["id"])

    if self.matcher.matches(msg["text"]):
        # ... 点赞逻辑
```

- [ ] **Step 2: 更新 last_checked_ids**

在本轮检测完成后:
```python
# 更新该群的 last_checked_ids
if messages:
    new_ids = [m["id"] for m in messages]
    self.state.update_last_checked_ids(group_name, new_ids)
```

- [ ] **Step 3: 传入 group_name 到 _get_messages**

调用处:
```python
messages = await self._get_messages(group_name if group_name else "")
```

---

### Task 4: 改进 _react 使用模拟鼠标+JS备选

**Files:**
- Modify: `main.py:475-511`

**Goal:** Hover失败时也能正确点赞

**Steps:**

- [ ] **Step 1: 改进工具栏查找逻辑**

```python
async def _react(self, message_element) -> bool:
    try:
        # 方法1: 尝试hover
        await message_element.hover()
        await self._delay(0.8, 1.2)
        toolbar = await message_element.query_selector(".messageAction__toolbar")

        if not toolbar:
            # 方法2: 用JS直接操作
            return await self._react_via_js(message_element)

        # 检查已点赞
        is_praised = await message_element.evaluate("""el => {
            const btn = el.querySelector('.toolbar-item.praise');
            return btn?.classList.contains('active')
                || btn?.querySelector('.icon-praise-full') !== null;
        }""")
        if is_praised:
            self.log("消息已点赞，跳过")
            return True

        # 点击点赞按钮
        reaction_btn = await toolbar.query_selector(".toolbar-item.praise")
        if reaction_btn:
            await reaction_btn.click()
            await self._delay(0.5, 1.0)
            return True

        return False
```

- [ ] **Step 2: 添加 JS 直接操作方法**

```python
async def _react_via_js(self, message_element) -> bool:
    """通过JS直接点击点赞按钮，不依赖工具栏渲染"""
    try:
        # 检查是否已点赞
        is_praised = await message_element.evaluate("""el => {
            const btn = el.querySelector('.toolbar-item.praise');
            return btn?.classList.contains('active')
                || btn?.querySelector('.icon-praise-full') !== null;
        }""")
        if is_praised:
            self.log("消息已点赞(JS)，跳过")
            return True

        # 通过JS点击点赞按钮
        result = await message_element.evaluate("""el => {
            const btn = el.querySelector('.toolbar-item.praise');
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        }""")
        if result:
            await self._delay(0.5, 1.0)
            return True

        self.log("未找到点赞按钮(JS)")
        return False
    except Exception as e:
        self.log(f"JS点赞异常: {e}")
        return False
```

- [ ] **Step 3: 添加模拟真实鼠标事件（备选）**

```python
async def _simulate_real_hover(self, element):
    """模拟真实鼠标移动"""
    try:
        box = await element.bounding_box()
        if not box:
            return False

        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2

        # 移动到元素位置
        await self._page.mouse.move(center_x, center_y)

        # 触发事件
        await element.dispatch_event('mouseenter')
        await element.dispatch_event('mouseover')

        await self._delay(0.5, 1.0)
        return True
    except Exception as e:
        self.log(f"模拟鼠标异常: {e}")
        return False
```

在 `_react` 开头调用:
```python
# 先尝试模拟真实鼠标
await self._simulate_real_hover(message_element)
```

---

### Task 5: 端到端测试验证

**Files:**
- Modify: `main.py` 整体测试

**验证点:**

- [ ] **验证1: 消息ID稳定性**

启动两次，检查 state.json 中同一条消息的ID是否相同

- [ ] **验证2: 不重复检测**

连续运行，检查日志中是否出现 "消息xxx没有匹配" 重复出现

- [ ] **验证3: 重启后继续检测**

模拟重启，检查是否继续检测新消息而非回溯旧消息

- [ ] **验证4: Hover失败时也能点赞**

在工具栏不显示时，能否通过JS方案点赞成功

---

## 执行方式

**Plan complete and saved to `docs/superpowers/plans/2026-04-10-message-detection-fix-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 我按任务逐个dispatch子agent，每个任务完成后review

**2. Inline Execution** - 在本session中顺序执行所有任务，我来批量执行

选择哪种方式？
