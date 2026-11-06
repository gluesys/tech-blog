#!/usr/bin/env bash
# Usage: tools/install_tools.sh <dest_dir> [--with-actionlint]
# Installs the pinned hugo (extended) and pagefind (extended) binaries into <dest_dir>.
# Exits non-zero if a download fails or a SHA-256 checksum does not match.
set -euo pipefail

with_actionlint=0
if [ $# -eq 2 ] && [ "$2" = "--with-actionlint" ]; then
  with_actionlint=1
elif [ $# -ne 1 ]; then
  echo "usage: $0 <dest_dir> [--with-actionlint]" >&2
  exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "$here/versions.env"

dest="$1"
mkdir -p "$dest"
dest="$(cd "$dest" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

fetch() { # url sha256 archive_name
  local url="$1" sha="$2" name="$3"
  curl -fsSL --retry 3 -o "$work/$name" "$url"
  (cd "$work" && echo "$sha  $name" | sha256sum -c -)
}

hugo_name="hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz"
fetch "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${hugo_name}" \
  "$HUGO_SHA256" "$hugo_name"
mkdir "$work/hugo"
tar -xzf "$work/$hugo_name" -C "$work/hugo" hugo
install -m 0755 "$work/hugo/hugo" "$dest/hugo"

pf_name="pagefind_extended-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz"
fetch "https://github.com/Pagefind/pagefind/releases/download/v${PAGEFIND_VERSION}/${pf_name}" \
  "$PAGEFIND_SHA256" "$pf_name"
mkdir "$work/pagefind"
tar -xzf "$work/$pf_name" -C "$work/pagefind"
install -m 0755 "$work/pagefind/pagefind_extended" "$dest/pagefind"

if [ "$with_actionlint" -eq 1 ]; then
  al_name="actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz"
  fetch "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${al_name}" \
    "$ACTIONLINT_SHA256" "$al_name"
  mkdir "$work/actionlint"
  tar -xzf "$work/$al_name" -C "$work/actionlint" actionlint
  install -m 0755 "$work/actionlint/actionlint" "$dest/actionlint"
fi

echo "Installed hugo ${HUGO_VERSION} and pagefind ${PAGEFIND_VERSION} into ${dest}"
