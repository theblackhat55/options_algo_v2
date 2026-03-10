from __future__ import annotations

import os

VALID_RUNTIME_MODES = {"mock", "live"}


def get_runtime_mode() -> str:
    mode = os.getenv("OPTIONS_ALGO_RUNTIME_MODE", "mock").strip().lower()

    if mode not in VALID_RUNTIME_MODES:
        raise ValueError("OPTIONS_ALGO_RUNTIME_MODE must be one of: mock, live")

    return mode


def is_mock_mode() -> bool:
    return get_runtime_mode() == "mock"
