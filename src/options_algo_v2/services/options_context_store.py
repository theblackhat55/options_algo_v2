from __future__ import annotations

import json
from pathlib import Path

from options_algo_v2.models.options_context import OptionsContextSnapshot


def write_latest_options_context_snapshot(
    snapshot: OptionsContextSnapshot,
    *,
    output_path: str | Path = "data/validation/latest_options_context.json",
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def append_options_context_history(
    snapshot: OptionsContextSnapshot,
    *,
    history_path: str | Path = "data/state/options_context_history.jsonl",
) -> Path:
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in snapshot.rows:
            fh.write(json.dumps(row.to_dict(), sort_keys=False) + "\n")
    return path
