import logging
import re
from typing import List, Optional, Pattern

# Configure logger for this module
logger = logging.getLogger(__name__)


class PatternMatcher:
    def __init__(self, patterns: Optional[List[str]] = None):
        self._compiled: List[Pattern] = []
        patterns = patterns or []

        successful_compiles = 0
        failed_patterns = []

        for raw in patterns:
            try:
                # Always treat patterns as regex (case-insensitive)
                compiled = re.compile(raw, re.IGNORECASE)
                self._compiled.append(compiled)
                successful_compiles += 1
            except re.error as e:
                failed_patterns.append((raw, str(e)))

        # Log warnings for failed compilations
        if failed_patterns:
            if successful_compiles == 0 and len(patterns) > 0:
                # Only pattern failed to compile
                raw, error = failed_patterns[0]
                logger.error(
                    f"Pattern compilation failed and no valid patterns remain. "
                    f"Pattern: '{raw}', Error: {error}. "
                    f"Please fix your settings."
                )
            else:
                # Some patterns succeeded, log warnings for failures
                for raw, error in failed_patterns:
                    logger.warning(
                        f"Pattern compilation failed, skipping: '{raw}', Error: {error}"
                    )

    def matches(self, text: str) -> bool:
        for compiled_pattern in self._compiled:
            if compiled_pattern.search(text):
                logger.info(
                    f"Match found: text='{text}' matched pattern='{compiled_pattern.pattern}'"
                )
                return True
        return False

    def get_matching_pattern(self, text: str) -> Optional[str]:
        """Return the first pattern that matches the text, or None if no match.

        Args:
            text: The text to match against patterns

        Returns:
            The pattern string that matched, or None if no match
        """
        for compiled_pattern in self._compiled:
            if compiled_pattern.search(text):
                return compiled_pattern.pattern
        return None
