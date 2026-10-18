#!/bin/bash
# SPDX-License-Identifier: LGPL-2.1-or-later

# release.sh <version>    publish main as <version> on the release branch
#
# Development happens on main, the Addon Manager installs from release. Each
# branch keeps its own package.xml (version, date and the branch its <url>
# names), so a plain merge would carry main's values over. This merges main
# into release, rewrites package.xml for the release, tags v<version>, and
# moves main on to the next patch version with a -dev suffix.
# Nothing is pushed; the command to do that is printed at the end.

set -euo pipefail
msg() { printf '\n\033[33;1m  Release\033[00m  %s\n\n' "$*"; }

version=${1:-}
[[ $version =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]] || { msg 'Usage: release.sh <major.minor.patch>'; exit 1; }
next="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))-dev"
today=$(date +%Y-%m-%d)

cd "$(dirname "${BASH_SOURCE[0]}")"
[[ $(git branch --show-current) == main ]] || { msg 'Run this from main'; exit 1; }
[[ -z $(git status --porcelain) ]] || { msg 'Commit or stash your changes first'; exit 1; }
git rev-parse -q --verify "refs/tags/v$version" >/dev/null && { msg "Tag v$version already exists"; exit 1; }

# set_manifest <version> <branch>
set_manifest() {
  sed -i \
    -e "s#<version>[^<]*</version>#<version>$1</version>#" \
    -e "s#<date>[^<]*</date>#<date>$today</date>#" \
    -e "s#branch=\"[^\"]*\"#branch=\"$2\"#" \
    -e "s#/blob/[^/]*/README.md#/blob/$2/README.md#" \
    package.xml
}

if git rev-parse -q --verify refs/heads/release >/dev/null; then
  git checkout -q release
  # package.xml always conflicts or carries main's values; it's rewritten below
  git merge -q --no-ff --no-commit main >/dev/null || true
  git checkout main -- package.xml
  if [[ -n $(git diff --name-only --diff-filter=U) ]]; then
    msg 'Merge conflicts besides package.xml, resolve them, then commit and tag by hand'
    exit 1
  fi
else
  git checkout -q -b release
fi

set_manifest "$version" release
git add package.xml
git commit -q -m "Release v$version"
git tag -a "v$version" -m "v$version"

git checkout -q main
set_manifest "$next" main
git commit -q -am "Start $next"

msg "Released v$version, main is now at $next"
echo "  git push origin main release v$version"
echo
