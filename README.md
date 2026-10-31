<img src="assets/icon.svg" width="64" height="64" alt="">

# t3-import

Import an existing Claude Code, Codex, or OpenCode 2 conversation into [T3 Code](https://github.com/pingdotgg/t3code)
and continue its native session. This repository contains a patch for T3 stable
`v0.1.3`, a reproducible build script, and Python helpers for selecting sessions.
It is an independent project, not an official T3 release.

The patch preserves the selected conversation branch, exposed reasoning, tool activity,
attachments, subagent activity, and compaction markers. It also fixes Claude's first
follow-up after import so the provider resumes the existing session.

## Requirements

- Linux with `/proc`, Bash, Git, and Python 3.10 or newer. The helpers have been
  exercised on Linux; macOS and Windows are not supported by the current helpers.
- Node **26.12.1** and pnpm **12.14.0**, matching the pinned upstream checkout.
  Install Node with your preferred version manager, then install pnpm with
  `npm install --global pnpm@12.14.0`.
- An authenticated installation of the provider you want to continue: Claude Code,
  Codex, or OpenCode **2**. Codex native APIs were exercised with CLI **0.166.0**;
  OpenCode with **2.0.28** (`@opencode/cli`, separate from the 1.x package).
- Claude sessions in `~/.claude` or `CLAUDE_CONFIG_DIR`; Codex/OpenCode use the
  provider instance configured in the separate T3 server.
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

## Codex and OpenCode 2

Open the separate T3 server and configure the relevant provider under **Settings >
Providers**. Enable OpenCode and point its binary path at an OpenCode 2 binary, or
configure an existing OpenCode 2 server URL and password. Installing OpenCode 2 can
migrate its database; follow OpenCode's migration guidance before replacing 1.x.
This importer rejects 1.x exports.

List and import through the provider's native history API:

```bash
python3 scripts/stable.py sessions --provider codex
python3 scripts/stable.py import SESSION_ID --provider codex
python3 scripts/stable.py sessions --provider opencode
python3 scripts/stable.py import SESSION_ID --provider opencode
```

For a named provider instance/account, pass its T3 instance ID consistently:

```bash
python3 scripts/stable.py sessions --provider codex --instance codex-personal
python3 scripts/stable.py import SESSION_ID --provider codex --instance codex-personal
```

The default instance IDs are `codex` and `opencode`. The importer checks that the
selected instance belongs to the requested provider and that the native workspace
matches the destination project. It never selects another account automatically.
Secrets stay in the server's provider configuration; listing returns session
metadata only.

Codex history comes from `thread/read`, with full turn pagination when required,
including archived sessions. OpenCode 2 history comes from its complete session
export, respecting any revert boundary. Imports use stable snapshots; active
sessions, changes during the read, missing local images, incomplete history, and
exceeded limits fail rather than producing a partial successful import.

Close the source conversation before importing, including other provider processes
that might write to it. Provider APIs do not offer a global lock across independent
CLI processes. `--force` is only available for the existing Claude open-session
check and cannot bypass native API checks.

## Continuing an imported conversation

Continuation binds to the original native session and writes new turns to its
provider history. Keep the original provider data available and use the same T3
provider instance. Avoid using the session in its CLI and T3 at the same time.
For Claude, the helper refuses sessions registered as open; `--force` bypasses
that Claude-specific check.

Importing the same session again returns the existing thread link. It does not
refresh the displayed transcript or synchronize subsequent changes in the provider.
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
| Attachments | Persists inline images, Codex local images, and OpenCode binary files. Missing referenced local images fail the import. Remote images are not downloaded. |
| Codex | Native full history and archived listing; commands/exit codes, multi-file diffs, plans, exposed reasoning, MCP/unknown tool records, compactions, and delegation activity. Native turn IDs are retained. |
| OpenCode 2 | Complete projected exports, ordered text/reasoning/tools, shell output, files, control messages, compactions, and revert boundaries. Tool rendering uses T3’s live OpenCode mapper. |
| Native API limits | 512 MiB per snapshot, 100,000 projected messages, and 1,000 pages per paginated operation. Limits fail explicitly; history is not silently truncated. |
| Model selection | Uses the exposed native model ID. If the API omits it, T3 uses its default; select the desired model before continuing. |
| Provider-private data | Encrypted reasoning and provider-private context/artifacts are not recoverable through the exposed history API. Child-session activity/results are shown; child conversations are imported separately. |
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

## Credits

- [T3 Code](https://github.com/pingdotgg/t3code) by T3 Tools Inc. provides the
  native scanner, importer, provider adapters, and application extended by this patch.
- [CarlosGtrz/t3-import](https://github.com/CarlosGtrz/t3-import) provided an
  important reference for Claude transcript parsing. Its
  [Claude parser](https://github.com/CarlosGtrz/t3-import/blob/5e20fb5709aa7ad6ce0853e210426c551066d7e0/src/sources/claude.ts)
  informed our conversation-branch selection and compaction handling, adapted here
  to T3's v2 import service. Thanks to Carlos and the t3-import contributors.
- [rafay99-epic/claude-code-to-t3](https://github.com/rafay99-epic/claude-code-to-t3)
  was also reviewed during compatibility research.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for source references and
upstream license notices.

## Development and verification

See [CONTRIBUTING.md](CONTRIBUTING.md) for focused tests, patch regeneration, and
pull requests. Verification covers synthetic parsing, native API pagination and
snapshot checks, database projections, attachments, ownership, and idempotency.
Live protocol checks use disposable provider homes; they do not certify every
provider version or encrypted/private data. Browser rendering and other operating
systems have not been verified.

Project code is [MIT licensed](LICENSE). T3 Code's copyright and license are
preserved in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
