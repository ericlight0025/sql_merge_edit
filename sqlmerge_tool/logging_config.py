"""集中管理 logging 設定。"""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """設定全域 logging 格式。"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
