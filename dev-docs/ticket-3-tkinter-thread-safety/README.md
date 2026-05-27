# Ticket 3: 数据库合并与 GUI 线程安全修复

**Branch**: `fix/message-db`  
**Date**: 2026-05-25  
**Status**: ✅ Completed

---

## 问题 1: Message 表分离存储

### 现象
`messages.db` 和 `app.db` 分开存储，与项目使用单一数据库的架构目标不符。

### 解决方案

**文件**: `src/parkbot/infra/config_di.py`

```python
# 删除
MESSAGES_DB_PATH = "messages.db"

# 添加共享引擎单例
_engine: Engine | None = None

def _get_engine() -> Engine:
    """Get or create the shared database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{DB_PATH}")
    return _engine

# 两个 repository 共享同一引擎
def get_settings_repository() -> AppSettingsRepository:
    engine = _get_engine()  # 使用共享引擎
    ...

def get_message_repository() -> IFeishuMessageRepository:
    engine = _get_engine()  # 使用共享引擎
    ...
```

---

## 问题 2: GUI 启动后崩溃 (Exit Code 139)

### 现象
`uv run python src/parkbot/main.py` 启动后，窗口显示约 2 秒后闪退，Exit code: 139 (SIGSEGV)。

### 根因分析

**Tkinter 不是线程安全的**。

`InstallTab._start_env_check()` 启动后台线程执行环境检查，检查结果通过回调 (`log_message`, `update_status`) 直接更新 GUI，违反了 Tkinter 的线程安全规则。

### 最小复现代码

```python
import customtkinter as ctk
import threading
import time

root = ctk.CTk()
label = ctk.CTkLabel(root, text="Test")
label.pack()

def unsafe_update():
    time.sleep(0.1)
    label.configure(text="Crash!")  # 后台线程调用 GUI 方法 → 段错误

threading.Thread(target=unsafe_update, daemon=True).start()
root.mainloop()  # Exit code 139
```

### 修复方案

**文件**: `src/parkbot/gui/tabs/install_tab.py`

所有 GUI 更新方法改为使用 `after()` 调度到主线程：

```python
def _safe_update(self, widget_update_func):
    """Schedule GUI update on main thread (thread-safe)."""
    self._tab.after(0, widget_update_func)

def update_status(self, key, status):
    if key in self.install_items:
        def do_update():
            self.install_items[key].configure(text=status)
        self._safe_update(do_update)

def log_message(self, msg):
    def do_log():
        self.install_log.configure(state="normal")
        self.install_log.insert("end", f"{msg}\n")
        self.install_log.see("end")
        self.install_log.configure(state="disabled")
    self._safe_update(do_log)

def set_button_state(self, enabled, text=None):
    def do_update():
        state = "normal" if enabled else "disabled"
        self.install_btn.configure(state=state)
        if text:
            self.install_btn.configure(text=text)
    self._safe_update(do_update)
```

### 测试修复

**文件**: `tests/gui/tabs/test_install_tab.py`

由于方法改为异步调度，测试需要 mock `after()` 来立即执行回调：

```python
def test_update_status(self):
    tab = MagicMock()

    # Mock after() to execute callback immediately
    def mock_after(delay, callback):
        if callable(callback):
            callback()
    tab.after = mock_after

    with patch("threading.Thread"):
        install = InstallTab(tab, ...)

    install.update_status("python", "✅ 已安装")
    install.install_items["python"].configure.assert_called_with(text="✅ 已安装")
```

---

## 验证

### 功能测试
```bash
# 应用正常启动和运行
uv run python src/parkbot/main.py

# 数据库只生成 app.db
ls -la *.db
# app.db (messages.db 不再生成)
```

### 单元测试
```bash
uv run pytest tests/ -q
# 228 passed
```

---

## 关键学习

1. **Exit Code 139** = Linux Segmentation Fault，通常是 C 层崩溃，Python 代码中常见原因是：
   - 调用 C 扩展时的内存问题
   - **非主线程操作 GUI (Tkinter)** ← 本次问题

2. **Tkinter 线程安全规则**:
   - ✅ 主线程创建和更新 GUI
   - ✅ 后台线程使用 `widget.after(0, callback)` 调度更新
   - ❌ 后台线程直接调用 `widget.configure()` 等方法

3. **调试技巧**:
   - 无 traceback 的崩溃 → 考虑 C 扩展/线程问题
   - 时间相关性 (启动后固定时间崩溃) → 考虑定时器/线程
   - 使用 `timeout` 命令运行程序捕获 exit code
