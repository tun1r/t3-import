#!/usr/bin/env python3
"""Run the patched stable build and import Claude Code, Codex, or OpenCode 2 sessions."""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
BASE = RUNTIME / "stable"
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
CLI = ROOT / "vendor/t3code/apps/server/dist/bin.mjs"
PID_FILE = RUNTIME / "stable.pid"
PORT = 3784
ORIGIN = f"http://127.0.0.1:{PORT}"


def owned_pid():
    try:
        pid = int(PID_FILE.read_text())
        args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        return pid if os.fsencode(CLI) in args and os.fsencode(BASE) in args else None
    except (OSError, ValueError):
        return None


def ready():
    try:
        with urllib.request.urlopen(ORIGIN + "/.well-known/t3/environment", timeout=1) as res:
            return res.status == 200
    except OSError:
        return False


def start():
    if owned_pid() and ready():
        return
    if not CLI.is_file():
        raise RuntimeError("Build stable first: bash scripts/build-stable.sh")
    with socket.socket() as sock:
        # Refuse to replace another server; closed connections may still be in TIME_WAIT.
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", PORT))
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    env = os.environ.copy()
    for key in ["T3CODE_HOME", "T3CODE_PORT", "VITE_DEV_SERVER_URL", "VITE_HTTP_URL",
                "VITE_WS_URL", "T3CODE_DEV_AUTH_TOKEN"]:
        env.pop(key, None)
    env["CLAUDE_CONFIG_DIR"] = str(CLAUDE)
    env["T3CODE_TAILSCALE_SERVE"] = "false"
    with (RUNTIME / "stable.log").open("ab", buffering=0) as log:
        os.chmod(log.name, 0o600)
        child = subprocess.Popen(
            ["node", str(CLI), "serve", "--base-dir", str(BASE),
             "--host", "127.0.0.1", "--port", str(PORT)],
            cwd=ROOT / "vendor/t3code", env=env, stdout=log, stderr=log,
            start_new_session=True,
        )
    PID_FILE.write_text(str(child.pid))
    for _ in range(120):
        if child.poll() is not None:
            raise RuntimeError("Stable server exited; see .runtime/stable.log")
        if ready():
            return
        time.sleep(0.25)
    raise RuntimeError("Stable server is still starting; see .runtime/stable.log")


def stop():
    pid = owned_pid()
    if pid is None:
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(120):
        if not ready():
            PID_FILE.unlink(missing_ok=True)
            return
        time.sleep(0.25)
    raise RuntimeError("Stable server has not stopped; see .runtime/stable.log")


def cli_json(*args):
    result = subprocess.run(["node", str(CLI), *args, "--base-dir", str(BASE)],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def open_app():
    start()
    # Keep the one-time credential out of terminal output and version control.
    url = cli_json("auth", "pairing", "create", "--base-url", ORIGIN, "--ttl", "5m",
                   "--json")["pairUrl"]
    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def session_files():
    return sorted((CLAUDE / "projects").glob("*/*.jsonl"),
                  key=lambda path: path.stat().st_mtime, reverse=True)


def session_details(path):
    cwd = None
    with path.open("rb") as file:
        for line in file:
            cwd = json.loads(line).get("cwd") if b'"cwd"' in line else None
            if cwd:
                break
        # Claude rewrites title records throughout a session; the tail has the latest.
        file.seek(max(0, path.stat().st_size - 512 * 1024))
        titles = {}
        for line in file.read().splitlines():
            if b'"custom-title"' in line or b'"ai-title"' in line:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue  # The seek can land mid-record.
                titles[record.get("type")] = record.get("customTitle") or record.get("aiTitle")
    return cwd, titles.get("custom-title") or titles.get("ai-title") or ""


def open_session_ids():
    """Claude registers every running session; the start time guards against PID reuse."""
    ids = set()
    for entry in (CLAUDE / "sessions").glob("*.json"):
        try:
            session = json.loads(entry.read_text())
            stat = Path(f"/proc/{session['pid']}/stat").read_text()
            if stat.rsplit(")", 1)[1].split()[19] == str(session.get("procStart")):
                ids.add(session["sessionId"])
        except (OSError, ValueError, KeyError, IndexError):
            continue
    return ids


def issue_token():
    start()
    return subprocess.run(
        ["node", str(CLI), "auth", "session", "issue", "--base-dir", str(BASE), "--ttl", "15m",
         "--label", "t3-import", "--token-only"],
        capture_output=True, text=True, check=True).stdout.strip()


def native_sessions(provider, instance, token):
    payload = {"source": provider}
    if instance:
        payload["providerInstanceId"] = instance
    return api(token, "POST", "/api/agent-sessions/list", payload)["sessions"]


def list_sessions(provider="claudeAgent", instance=None):
    if provider != "claudeAgent":
        for session in native_sessions(provider, instance, issue_token()):
            print(f"{session['sessionId']}  {session['updatedAt']}  "
                  f"{session['providerInstanceId']}  {session['title'][:50]}  "
                  f"{session['workspaceRoot']}")
        return
    running = open_session_ids()
    for path in session_files():
        cwd, title = session_details(path)
        updated = time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))
        size = f"{path.stat().st_size / 1_000_000:.0f} MB"
        state = "open" if path.stem in running else ""
        print(f"{path.stem}  {updated}  {size:>7}  {state:4}  {title[:50]:50}  {cwd or '?'}")


def api(token, method, route, payload=None):
    request = urllib.request.Request(
        ORIGIN + route, method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"authorization": f"Bearer {token}", "content-type": "application/json",
                 "x-t3-orchestration-protocol": "2"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{method} {route} failed ({error.code}): "
                           f"{error.read().decode(errors='replace')[:500]}") from None


def import_session(session_id, force=False, provider="claudeAgent", instance=None):
    if provider == "claudeAgent":
        path = next((path for path in session_files() if path.stem == session_id), None)
        if path is None:
            raise RuntimeError(f"No Claude session {session_id} under {CLAUDE / 'projects'}")
        if session_id in open_session_ids() and not force:
            raise RuntimeError("That session is still open in Claude Code. Close it first, so "
                               "Claude Code and T3 do not both write to it, or pass --force.")
        cwd, title = session_details(path)
        provider_instance = "claudeAgent"
        token = None
    else:
        if force:
            raise RuntimeError("--force applies only to Claude; native API snapshot checks cannot be bypassed.")
        token = issue_token()
        session = next((s for s in native_sessions(provider, instance, token)
                        if s["sessionId"] == session_id), None)
        if session is None:
            raise RuntimeError(f"No {provider} session {session_id} in the selected provider instance")
        cwd, title = session["workspaceRoot"], session["title"]
        provider_instance = session["providerInstanceId"]
    if not cwd or not Path(cwd).is_dir():
        raise RuntimeError(f"The session's folder no longer exists: {cwd or 'unknown'}")
    workspace = str(Path(cwd).resolve())
    token = token or issue_token()
    projects = api(token, "GET", "/api/projects")["projects"]
    project = next((project for project in projects if project["deletedAt"] is None and
                    str(Path(project["workspaceRoot"]).resolve()) == workspace), None)
    if project is None:
        project = api(token, "POST", "/api/projects/mutate", {
            "type": "project.create", "commandId": str(uuid.uuid4()),
            "projectId": str(uuid.uuid4()), "title": Path(workspace).name,
            "workspaceRoot": workspace,
        })
        print(f"Created project {project['title']} for {workspace}")
    thread_id = urllib.parse.quote(f"import:{provider_instance}:{session_id}", safe="")
    link = f"{ORIGIN}/{(BASE / 'userdata/environment-id').read_text().strip()}/{thread_id}"
    try:
        api(token, "GET", f"/api/orchestration/threads/{thread_id}")
        print(f"{title or session_id} is already in T3 under {project['title']}")
        return link
    except RuntimeError as error:
        if "(404)" not in str(error):
            raise
    result = api(token, "POST", "/api/agent-sessions/import", {
        "projectId": project["id"], "expectedWorkspaceRoot": project["workspaceRoot"],
        "sessionId": session_id, "includeOlder": True, "source": provider,
        "providerInstanceId": provider_instance,
    })
    if result["importedCount"] == 0:
        raise RuntimeError("Nothing imported: a history limit or native-session ownership "
                           "check prevented the import; see .runtime/stable.log.")
    print(f"Imported {title or session_id} into {project['title']}")
    return link


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="open",
                        choices=["start", "stop", "restart", "status", "open", "sessions",
                                 "import"])
    parser.add_argument("session_id", nargs="?", help="Native session ID for import")
    parser.add_argument("--force", action="store_true",
                        help="import even if the session is still open in Claude Code")
    parser.add_argument("--provider", choices=["claudeAgent", "codex", "opencode"],
                        default="claudeAgent", help="session source; opencode requires OpenCode 2")
    parser.add_argument("--instance", help="configured T3 provider instance ID for Codex/OpenCode")
    args = parser.parse_args()
    if args.instance and args.provider == "claudeAgent":
        parser.error("--instance is currently supported for Codex and OpenCode 2")
    if args.command == "sessions":
        return list_sessions(args.provider, args.instance)
    if args.command == "import":
        if not args.session_id:
            parser.error("import needs a session ID; list them with: stable.py sessions")
        return print(import_session(args.session_id, args.force, args.provider, args.instance))
    if args.command in ["stop", "restart"]:
        stop()
    if args.command in ["start", "restart"]:
        start()
    if args.command == "open":
        open_app()
    running = owned_pid() is not None and ready()
    print(f"T3 Import Stable: {'running at ' + ORIGIN if running else 'stopped'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        raise SystemExit(str(error))
