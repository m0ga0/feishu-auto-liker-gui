import re
from typing import Callable, List, Optional, Pattern, Union


class PatternMatcher:
    def __init__(self, patterns: List[str], log_callback: Optional[Callable] = None):
        self._compiled: List[tuple[bool, Union[Pattern, str]]] = []
        self.log = log_callback or (lambda msg: None)
        for raw in patterns:
            if raw.startswith("re:"):
                try:
                    self._compiled.append((True, re.compile(raw[3:], re.IGNORECASE)))
                except re.error:
                    pass
            else:
                self._compiled.append((False, raw))

    def matches(self, text: str) -> bool:
        for is_regex, pattern in self._compiled:
            is_match = False
            if is_regex:
                assert isinstance(pattern, re.Pattern)
                if pattern.search(text):
                    is_match = True
            else:
                assert isinstance(pattern, str)
                if pattern in text:
                    is_match = True

            if is_match:
                return True
        return False