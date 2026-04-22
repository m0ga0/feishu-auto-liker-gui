import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from ..config import STATE_PATH


class BotState:
    def __init__(self):
        self._seen_ids: Set[str] = set()
        self._group_states: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time: Optional[float] = None
        self.recent_logs: List[str] = []
        self.is_running = False
        self._load_state()

    def get_group_state(self, group_name: str) -> Dict:
        if group_name not in self._group_states:
            self._group_states[group_name] = {
                "seen_ids": set(),
                "reacted_ids": set(),
                "last_checked_ids": [],
                "last_check_time": 0,
            }
        return self._group_states[group_name]

    def mark_seen(self, group_name: str, msg_id: str) -> None:
        gs = self.get_group_state(group_name)
        gs["seen_ids"].add(msg_id)
        self._save_state()

    def is_seen(self, group_name: str, msg_id: str) -> bool:
        gs = self.get_group_state(group_name)
        return msg_id in gs["seen_ids"]

    def mark_reacted(self, group_name: str, msg_id: str) -> None:
        gs = self.get_group_state(group_name)
        gs["reacted_ids"].add(msg_id)
        self._save_state()

    def is_reacted(self, group_name: str, msg_id: str) -> bool:
        gs = self.get_group_state(group_name)
        return msg_id in gs["reacted_ids"]

    def update_last_checked_ids(self, group_name: str, ids: List[str]) -> None:
        gs = self.get_group_state(group_name)
        gs["last_checked_ids"] = ids
        gs["last_check_time"] = time.time()
        self._save_state()

    def get_last_checked_ids(self, group_name: str) -> List[str]:
        gs = self.get_group_state(group_name)
        return gs.get("last_checked_ids", [])

    def _load_state(self) -> None:
        if STATE_PATH.exists():
            try:
                data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                groups_data = data.get("groups", {})
                for name, state in groups_data.items():
                    self._group_states[name] = {
                        "seen_ids": set(state.get("seen_ids", [])),
                        "reacted_ids": set(state.get("reacted_ids", [])),
                        "last_checked_ids": state.get("last_checked_ids", []),
                        "last_check_time": state.get("last_check_time", 0),
                    }
                logger.info(f"已加载 {len(self._group_states)} 个群组的状态")
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")

    def _save_state(self) -> None:
        try:
            data = {
                "groups": {
                    name: {
                        "seen_ids": list(state.get("seen_ids", set())),
                        "reacted_ids": list(state.get("reacted_ids", set())),
                        "last_checked_ids": state.get("last_checked_ids", []),
                        "last_check_time": state.get("last_check_time", 0),
                    }
                    for name, state in self._group_states.items()
                }
            }
            STATE_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"保存状态文件失败: {e}")

    def log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.recent_logs.append(entry)
        self.recent_logs = self.recent_logs[-100:]

    def reset(self) -> None:
        self.match_count = 0
        self.reaction_count = 0
        self.fail_count = 0
        self.start_time = None
        self.is_running = False
        self.recent_logs.clear()

    @property
    def uptime(self) -> str:
        if not self.start_time:
            return "0秒"
        total = int(time.time() - self.start_time)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}小时{m}分{s}秒"
        elif m > 0:
            return f"{m}分{s}秒"
        return f"{s}秒"