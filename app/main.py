"""Application entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence, TextIO

from app.storage import RuleStorageError, load_rules


DEFAULT_RULES_PATH = Path("rules.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="macro-tool",
        description="Image-recognition desktop macro tool.",
    )
    parser.add_argument(
        "--rules",
        default=str(DEFAULT_RULES_PATH),
        help="Path to the rule JSON file.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Start the PySide6 GUI.",
    )
    return parser


def main(argv: Sequence[str] | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    """Load application configuration and start the application placeholder."""
    output = sys.stdout if stdout is None else stdout
    error_output = sys.stderr if stderr is None else stderr
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        rule_set = load_rules(args.rules)
    except RuleStorageError as error:
        print(f"Error: {error}", file=error_output)
        return 1

    if args.gui:
        try:
            from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]

            from app.ui.main_window import create_main_window
        except ImportError:
            print("Error: PySide6 is not installed.", file=error_output)
            return 1

        app = QApplication(list(argv or []))
        window = create_main_window(rule_set, rules_path=args.rules)
        window.show()
        return app.exec()

    print(f"Macro Tool core is ready. Loaded {len(rule_set.rules)} rule(s).", file=output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
