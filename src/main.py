#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import job_manage, launch, resume, runner, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EvoBench OpenHands Python CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    launch.add_parser(subparsers)
    runner.add_parser(subparsers)
    summarize.add_parser(subparsers)
    job_manage.add_parser(subparsers)
    resume.add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
