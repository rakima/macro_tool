"""GUI entry point for packaged builds."""

from __future__ import annotations

import sys

from app.main import main


def run() -> int:
    args = list(sys.argv[1:])
    if "--gui" not in args:
        args.append("--gui")
    return main(args)


if __name__ == "__main__":
    raise SystemExit(run())
