<img src="assets/icon.svg" width="64" height="64" alt="">

# t3-import

Import an existing Claude Code conversation into [T3 Code](https://github.com/pingdotgg/t3code)
and continue its native session. This repository contains a patch for T3 stable
`v0.1.3`, a reproducible build script, and Python helpers for selecting sessions.
It is an independent project, not an official T3 release.

The patch preserves the selected conversation branch, tool activity, thinking,
inline images, subagents, and compaction markers. It also fixes Claude's first
follow-up after import so the provider resumes the existing session.

## Requirements

- Linux with `/proc`, Bash, Git, and Python 3.10 or newer. The helpers have been
  exercised on Linux; macOS and Windows are not supported by the current helpers.
- Node **26.12.1** and pnpm **12.14.0**, matching the pinned upstream checkout.
  Install Node with your preferred version manager, then install pnpm with
  `npm install --global pnpm@12.14.0`.
- A working, authenticated Claude Code installation with sessions in `~/.claude`,
  or in the directory specified by `CLAUDE_CONFIG_DIR`.
- A browser and `xdg-open` to use the `open` command.
- Internet access for the initial upstream clone and dependency installation.
  Native dependency builds may also require your distribution's C/C++ build tools.

The stable helper builds and runs a separate T3 server. An installed T3 desktop
application is not required.

## Quick start

```bash
git clone https://github.com/tun1r/t3-import.git
cd t3-import
node --version
pnpm --version
bash scripts/build-stable.sh
python3 scripts/stable.py sessions
```

Close the conversation in Claude Code, then replace `SESSION_ID` below with an ID
from the list:

```bash
python3 scripts/stable.py import SESSION_ID
python3 scripts/stable.py open
```

`import` starts the server if needed, finds or creates a T3 project for the
session's original folder, imports the selected session, and prints its thread
link. `open` opens a temporary pairing link in your browser. After pairing, use the
printed thread link or select the imported conversation in T3.

The server listens at **http://127.0.0.1:3784**. Its state lives in
`.runtime/stable`, separately from an installed nightly's data. Keep this checkout
if you want to retain that state.

## Continuing an imported conversation

Continuation resumes the original Claude session and writes new turns to its
provider history. Keep the original Claude session files available. Avoid using
that session in Claude Code and T3 at the same time. The helper refuses sessions
registered as open in Claude Code; `--force` bypasses that check.

Importing the same session again returns the existing thread link. It does not
refresh the displayed transcript or synchronize subsequent Claude Code changes.
A deleted T3 thread can still reserve its native session ID; deleting the visible
thread does not guarantee that the same ID can be imported again.

The session's recorded project folder must still exist. Importing does not restore
an old Git branch, worktree, or uncommitted files. Continuation uses the workspace
as it exists now.

## Server commands

```bash
python3 scripts/stable.py start
python3 scripts/stable.py status
python3 scripts/stable.py restart
python3 scripts/stable.py stop
python3 scripts/stable.py --help
```

After a reboot, run `python3 scripts/stable.py open` again. The helper starts the
server as a background process and records its PID and log under `.runtime`.
`stop` stops only a server matching this checkout's recorded command and data path.

To use another Claude configuration, set the variable consistently for listing,
importing, and running the server:

```bash
export CLAUDE_CONFIG_DIR=/path/to/claude-config
python3 scripts/stable.py sessions
python3 scripts/stable.py import SESSION_ID
```

Stop an existing helper server before changing its Claude configuration.

## Scope and limits

| Area | Behavior |
| --- | --- |
| Supported build | Upstream `v0.1.3`, commit `d2c440312e5f39d59827ed466838a623516454d6`. The build script checks the commit before applying the patch. |
| Claude branches | Imports the selected/current branch. Alternate historical branches are not separate resumable T3 threads. |
| Displayed activity | Text, supported tools, thinking, inline images, subagents, and compaction markers. Trailing tool activity after the last visible message is omitted. |
| Selected-session limits | Up to 512 MiB of selected conversation data, 1,000,000 records, and 100,000 messages. File size alone does not determine this budget. |
| Images | Persists inline image bytes; does not download remote images. |
| Codex | The server patch handles Codex import and tool activity; the Python selection helper is Claude-only. Native Codex continuation has not been verified here. |
| Installed desktop app | The stable build does not update or patch it. Nightly import requires the separate procedure below. |

## Installed nightly (advanced, Arch Linux only)

`scripts/nightly.py` is specific to the `t3code-nightly-bin` Arch package. It expects
`/opt/t3code-nightly-bin/t3code`, the `sqlite3` command, and a patched build matching
the installed nightly exactly. Prefer the separate stable server for initial use.

Check the installed package:

```bash
pacman -Q t3code-nightly-bin
```

Convert its version to the corresponding upstream tag: for example,
`0.1.4_nightly.20261027.3770-1` becomes `v0.1.4-nightly.20261027.3770`.
With T3 completely closed, including its tray process, prepare that tag:

```bash
# Replace INSTALLED_NIGHTLY_TAG with the exact tag for your installed package.
git clone --depth 1 --branch INSTALLED_NIGHTLY_TAG https://github.com/pingdotgg/t3code.git vendor/t3code-nightly
git -C vendor/t3code-nightly apply --check ../../patches/stable-session-import.patch
git -C vendor/t3code-nightly apply ../../patches/stable-session-import.patch
cd vendor/t3code-nightly
pnpm install --frozen-lockfile
node_modules/.bin/vp run --filter t3 build
cd ../..
python3 scripts/nightly.py SESSION_ID
```

Use the toolchain required by that nightly's `package.json`. If the patch does not
apply cleanly, stop and port it to that version before importing. Compatibility
with arbitrary newer nightlies is not guaranteed.

The helper refuses an open app, a mismatched build, or running/queued database
work. It backs up `~/.t3/userdata/statev2.sqlite`, briefly runs the patched server
against the nightly data, imports, stops the temporary server, and relaunches the
installed app. The app's installed code remains unchanged; the imported data is
written to its real database. Review the script before using it on important data.

## Troubleshooting

- **Build missing:** run `bash scripts/build-stable.sh` first. The script clones
  upstream into the ignored `vendor/t3code` directory and builds the server/web UI.
- **Unexpected upstream revision or patch conflict:** use a fresh checkout of the
  pinned release. Save any local upstream edits before replacing `vendor/t3code`.
- **Port already in use:** stop the process using port 3784. The helper refuses to
  replace another server.
- **Session folder missing:** restore the original workspace path before importing.
- **Nothing imported:** inspect `.runtime/stable.log` for import-limit warnings or
  ownership conflicts. Nightly-import logs live under `.runtime/nightly-import`.
- **First follow-up fails in the installed nightly:** its provider code may still
  have the upstream first-resume bug. The separate patched stable build includes
  the fix; importing with a temporary patched server does not update app binaries.

Logs, databases, session files, credentials, and machine-specific investigation
notes are excluded from this repository. Before sharing a bug report, redact
session text, IDs, paths, pairing links, and tokens from any excerpts.

## Development and verification

See [CONTRIBUTING.md](CONTRIBUTING.md) for tests, patch regeneration, and pull
requests. On 2026-10-30, all 311 focused scanner/importer/JSON/Claude-adapter tests passed;
Python syntax, CLI help, shell syntax, and patch consistency checks also passed.
Earlier isolated Linux checks exercised a large transcript, idempotency, open-session
refusal, native continuation before/after restart, typecheck, lint, and production
build. Browser rendering and other operating systems were not verified.

Project code is [MIT licensed](LICENSE). T3 Code's copyright and license are
preserved in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
