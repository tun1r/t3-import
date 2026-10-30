#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
project_root=$PWD
upstream_commit=d2c440312e5f39d59827ed466838a623516454d6
mkdir -p vendor
if [[ ! -d vendor/t3code/.git ]]; then
  git clone --depth 1 --branch v0.1.3 https://github.com/pingdotgg/t3code.git vendor/t3code
fi
cd vendor/t3code
[[ "$(git rev-parse HEAD)" == "$upstream_commit" ]] || {
  echo 'Unexpected upstream revision; refusing to apply the stable patch.' >&2
  exit 1
}
if ! git apply --reverse --check "$project_root/patches/stable-session-import.patch" 2>/dev/null; then
  git apply --check "$project_root/patches/stable-session-import.patch"
  git apply "$project_root/patches/stable-session-import.patch"
fi
pnpm install --frozen-lockfile
node_modules/.bin/vp run --filter t3 build
