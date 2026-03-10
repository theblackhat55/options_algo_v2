from __future__ import annotations

from options_algo_v2.services.databento_runtime_info import (
    build_databento_runtime_info,
)


def show_databento_runtime_info() -> dict[str, str]:
    info = build_databento_runtime_info()

    print(f"dataset={info['dataset']}")
    print(f"schema={info['schema']}")
    print(f"has_api_key={info['has_api_key']}")

    return info


def main() -> None:
    show_databento_runtime_info()


if __name__ == "__main__":
    main()
