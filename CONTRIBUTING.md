# Contributing

Bug reports, documentation fixes, and focused importer improvements are welcome.
Read the [README](README.md) for requirements, setup, and current limitations.

## Set up a checkout

Fork the repository, clone your fork, and create a branch. Install the Node and
pnpm versions listed in the README, then run:

```bash
bash scripts/build-stable.sh
```

This checks out the pinned upstream T3 release, applies the importer patch, installs
its dependencies, and builds it under `vendor/t3code`. That directory is ignored;
changes there must be exported into the patch to be included in a pull request.
The Python helpers use only the standard library and need no virtual environment.

## Where changes belong

| Path | Purpose |
| --- | --- |
| `scripts/stable.py` | Linux session selection, project matching, API import, and stable-server lifecycle. |
| `scripts/nightly.py` | Arch-specific checks, database backup, temporary nightly import, and app relaunch. |
| `scripts/build-stable.sh` | Pinned upstream clone, patch application, and build. |
| `patches/stable-session-import.patch` | Server scanner/importer, native Claude resume fix, contracts, CLI/HTTP integration, tests, and upstream documentation. |
| `vendor/t3code/apps/server/src/project/` | Working copies of the scanner/importer and their tests after setup. |
| `vendor/t3code/apps/server/src/orchestration-v2/Adapters/ClaudeAdapterV2.ts` | Claude provider continuation and tool-item conversion. |

Keep changes focused on the importer. Preserve native session identity, workspace
checks, idempotency, and server event/projection invariants. Do not add direct
projection-table writes as a shortcut around the server's import service.

## Checks

From this repository's root:

```bash
python3 -m py_compile scripts/stable.py scripts/nightly.py
python3 scripts/stable.py --help
python3 scripts/nightly.py --help
bash -n scripts/build-stable.sh
```

For changes to the upstream patch, run the focused suite and server typecheck:

```bash
cd vendor/t3code
node_modules/.bin/vp test run \
  apps/server/src/project/AgentSessionScanner.test.ts \
  apps/server/src/project/AgentSessionImporter.test.ts \
  apps/server/src/project/AgentSessionJson.test.ts \
  apps/server/src/orchestration-v2/Adapters/ClaudeAdapterV2.test.ts
node_modules/.bin/vp run --filter t3 typecheck
```

Run lint on the upstream files you changed and rebuild when the change affects
runtime behavior or contracts:

```bash
# From vendor/t3code; replace paths with the source files you changed.
node_modules/.bin/vp lint apps/server/src/project/AgentSessionScanner.ts
node_modules/.bin/vp run --filter t3 build
```

Use small, synthetic transcripts for regression fixtures. Cover the behavior that
failed, including failure paths when relevant. An imported transcript appearing in
the sidebar does not prove native continuation works: for a continuation change,
verify that the provider resumes the native session, recalls earlier content, and
still resumes after a server restart.

For manual experiments, use a disposable source session and T3 data directory.
Do not use the nightly helper as a test runner: it writes to the installed app's
real data. Never submit personal transcripts, live database copies, credentials,
or unredacted logs as fixtures or attachments.

## Regenerate the patch

Make source edits in `vendor/t3code`. Confirm it is still at the pinned commit:

```bash
git -C vendor/t3code rev-parse HEAD
git -C vendor/t3code diff --stat HEAD
```

New upstream files need an intent-to-add entry (`git add -N path/to/new-file`, from
inside `vendor/t3code`) so they appear in `git diff`. Then, from this repository's
root:

```bash
git -C vendor/t3code diff --binary HEAD > patches/stable-session-import.patch
git -C vendor/t3code apply --reverse --check ../../patches/stable-session-import.patch
git -C vendor/t3code diff --check HEAD
```

Review the exported diff for unrelated upstream changes and local information.
Do not commit `vendor/`, build outputs, runtime state, or dependency directories.
Patch context lines can contain a single space; do not strip those spaces to
silence a whitespace warning on the patch file itself.

Before proposing a patch update, also check forward application against a fresh
checkout of the pinned upstream commit. Do not use a live app database to perform
this check. Changing the upstream pin requires updating the build script, README,
patch, and compatibility evidence together.

## Submit a change

Open a pull request against `main` describing the problem, the resulting behavior,
and the checks you ran. Include a small synthetic reproduction for importer bugs
when practical. State any checks you could not run and any compatibility limits.
Do not claim native resume or platform compatibility based only on unit tests.

For bug reports, include your OS, Node/pnpm versions, upstream T3 version, the
command used, and a redacted error. Keep conversation content, native IDs, personal
paths, access tokens, and browser pairing URLs out of public issues.

Contributions are provided under the repository's MIT license. Preserve upstream
copyright and license notices when modifying or redistributing T3-derived code.
