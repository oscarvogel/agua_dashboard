"""Load the host-provided dotenv file before starting the application."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import dotenv_values


SECRET_ENV_FILE = Path("/run/secrets/agua.env")


def main() -> None:
    if SECRET_ENV_FILE.is_file():
        for key, value in dotenv_values(SECRET_ENV_FILE).items():
            if key and value is not None:
                os.environ[key] = value

    if len(sys.argv) < 2:
        raise SystemExit("Usage: entrypoint.py COMMAND [ARGS...]" )

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
