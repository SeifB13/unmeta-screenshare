from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, config, i18n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="unmeta",
        description="Mirror a Meta Quest headset to this computer over Wi-Fi.",
    )
    parser.add_argument("--lang", choices=i18n.LANGUAGES, help="interface language")
    parser.add_argument("--config", type=Path, help="use this config file")
    parser.add_argument(
        "--print-config-path", action="store_true", help="print the config file path and exit"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    path = args.config or config.default_path()
    if args.print_config_path:
        print(path)
        return 0

    cfg = config.load(path)
    i18n.set_language(args.lang or cfg.language or i18n.detect_language())

    from .app import UnMetaApp  # after set_language: screens read strings at import time

    UnMetaApp(cfg, path).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
