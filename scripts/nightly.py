#!/usr/bin/env python3
"""Import a Claude Code session into the installed T3 nightly with the patched importer.

Quit T3 first. The patched build of the installed nightly commit briefly serves the
nightly's own data, imports the session, stops, and relaunches the nightly.
"""
import argparse
from pathlib import Path
import subprocess
import time

import stable

NIGHTLY_HOME = Path.home() / ".t3"
NIGHTLY_APP = Path("/opt/t3code-nightly-bin/t3code")
CHECKOUT = stable.ROOT / "vendor/t3code-nightly"
DATABASE = NIGHTLY_HOME / "userdata/statev2.sqlite"


def use_patched_nightly():
    stable.CLI = CHECKOUT / "apps/server/dist/bin.mjs"
    stable.BASE = NIGHTLY_HOME
    stable.RUNTIME = stable.ROOT / ".runtime/nightly-import"
    stable.PID_FILE = stable.RUNTIME / "server.pid"
    stable.PORT = 3797
    stable.ORIGIN = f"http://127.0.0.1:{stable.PORT}"


def require_matching_build():
    installed = subprocess.run(["pacman", "-Q", "t3code-nightly-bin"], capture_output=True,
                               text=True, check=True).stdout.split()[1].rsplit("-", 1)[0]
    tag = "v" + installed.replace("_", "-")
    built = subprocess.run(["git", "-C", str(CHECKOUT), "describe", "--tags", "--exact-match"],
                           capture_output=True, text=True).stdout.strip()
    if built != tag:
        raise RuntimeError(f"The patched build is {built or 'unknown'}, but the installed nightly "
                           f"is {tag}. Rebuild the patch on {tag} before importing.")
    if not stable.CLI.is_file():
        raise RuntimeError(f"Build the patched nightly first in {CHECKOUT}")


def require_nightly_closed():
    running = [pid for pid in Path("/proc").iterdir() if pid.name.isdigit()
               and _executable(pid) == str(NIGHTLY_APP)]
    if running:
        raise RuntimeError("T3 is still running. Quit it completely (including the tray icon) "
                           "and run this again.")


def _executable(pid):
    try:
        return str((pid / "exe").resolve())
    except OSError:
        return None


def require_idle_database():
    uri = f"file:{DATABASE}?mode=ro"
    busy = subprocess.run(["sqlite3", uri, """
        select (select count(*) from orchestration_v2_projection_runs where status = 'running')
             + (select count(*) from orchestration_v2_effect_outbox
                where status not in ('succeeded', 'failed', 'cancelled'));"""],
                          capture_output=True, text=True, check=True).stdout.strip()
    if busy != "0":
        raise RuntimeError("The nightly database still has running or queued work; open T3, "
                           "let it finish, quit, and try again. Importing now could restart it.")


def back_up_database():
    backup = DATABASE.with_name(f"statev2.sqlite.before-t3-import-{time.strftime('%Y%m%d-%H%M%S')}")
    subprocess.run(["sqlite3", str(DATABASE), f".backup '{backup}'"], check=True)
    print(f"Backed up the nightly database to {backup}")
    return backup


def relaunch_nightly():
    subprocess.Popen([str(NIGHTLY_APP)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    print("Relaunched T3 nightly")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id", help="Claude session ID; list them with stable.py sessions")
    parser.add_argument("--force", action="store_true",
                        help="import even if the session is still open in Claude Code")
    args = parser.parse_args()
    use_patched_nightly()
    require_matching_build()
    require_nightly_closed()
    require_idle_database()
    back_up_database()
    try:
        stable.import_session(args.session_id, args.force)
    finally:
        stable.stop()
        relaunch_nightly()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        raise SystemExit(str(error))
