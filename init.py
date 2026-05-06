#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///

import json, subprocess, sys
from pathlib import Path


def main():
    config_path = Path("config.json")
    if not config_path.exists():
        json.dump(
            {
                "status": "skipped",
                "message": "config.json not found, auth will happen on first tool use",
            },
            sys.stdout,
        )
        return
    config = json.loads(config_path.read_text())
    li_at = config.get("li_at")
    if not li_at:
        json.dump(
            {
                "status": "skipped",
                "message": "li_at not configured yet, auth will happen on first tool use",
            },
            sys.stdout,
        )
        return

    cli = (Path(__file__).resolve().parent / "bin" / "linkedin-cli").resolve()
    args = [str(cli), "auth", "login", "--li-at", li_at]
    cookies_file = config.get("cookies_file")
    if cookies_file:
        args.extend(["--cookies-file", str(cookies_file)])
    jsessionid = config.get("jsessionid")
    if jsessionid:
        args.extend(["--jsessionid", str(jsessionid)])
    li_gc = config.get("li_gc")
    if li_gc:
        args.extend(["--li-gc", str(li_gc)])
    bcookie = config.get("bcookie")
    if bcookie:
        args.extend(["--bcookie", str(bcookie)])
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        sys.stderr.buffer.write(result.stderr)
        sys.exit(result.returncode)

    output = result.stdout.decode().strip()
    json.dump({"status": "ok", "message": output}, sys.stdout)


main()
