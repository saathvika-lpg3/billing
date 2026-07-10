from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path


SQLITEDUMP_EXE = Path(r"C:\xampp\sqlite\bin\sqlitedump.exe")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a PRM_GST SQLite backup before desktop migration.")
    parser.add_argument("--database", default="prm_gst")
    parser.add_argument("--out-dir", default=r"D:\PRM_GST_DESKTOP\backups")
    args = parser.parse_args()

    if not SQLITEDUMP_EXE.exists():
        raise FileNotFoundError(f"SQLite dump tool not found: {SQLITEDUMP_EXE}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"{args.database}_sqlite_backup_{stamp}.sql"
    command = [
        str(SQLITEDUMP_EXE),
        "-uroot",
        "--routines",
        "--triggers",
        "--events",
        "--single-transaction",
        "--default-character-set=utf8mb4",
        args.database,
    ]
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        subprocess.run(command, stdout=handle, stderr=subprocess.PIPE, text=True, check=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
