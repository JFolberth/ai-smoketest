#!/usr/bin/env bash
# Install the latest actionlint binary into /usr/local/bin.
# Extracted from the devcontainer postCreateCommand so it survives failures
# on either the download or the extraction step with a readable error.
set -euo pipefail

VERSION="${ACTIONLINT_VERSION:-1.7.7}"
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64)  ARCH_TAG="amd64" ;;
  aarch64|arm64) ARCH_TAG="arm64" ;;
  *) echo "unsupported arch: $ARCH" >&2; exit 1 ;;
esac

TARBALL="actionlint_${VERSION}_linux_${ARCH_TAG}.tar.gz"
URL="https://github.com/rhysd/actionlint/releases/download/v${VERSION}/${TARBALL}"

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

curl -fsSL "$URL" -o "${TMPDIR}/${TARBALL}"
tar -xzf "${TMPDIR}/${TARBALL}" -C "${TMPDIR}" actionlint
sudo install -m 0755 "${TMPDIR}/actionlint" /usr/local/bin/actionlint
actionlint --version
