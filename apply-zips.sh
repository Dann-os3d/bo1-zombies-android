#!/bin/bash
# apply-zips.sh - upload this file and a patch zip to the repository's main folder (the root).
# For every *.zip found there it:
#   - with a *.patch inside: applies the patches in name order (already applied ones are skipped);
#   - without one: copies the zip's tree over the repository (a single top folder is stripped);
# then deletes the zip and commits. The workflow .github/workflows/apply-zips.yml runs it on GitHub;
# you can also run it by hand in a clone:  bash apply-zips.sh   (DRY_RUN=1 bash apply-zips.sh to only check).
#
# Settings (environment variables):
#   ZIP_GLOB  which zips to take, default "*.zip" (e.g. "bo1-*.zip")
#   DRY_RUN   1: check and report, change nothing
#   NO_PUSH   1: commit but do not push (by hand)
#   KEEP_ZIP  1: leave the zip in place
set -euo pipefail
shopt -s nullglob
cd "$(dirname "$0")"
ZIP_GLOB=${ZIP_GLOB:-*.zip}
zips=( $ZIP_GLOB )
if [ ${#zips[@]} -eq 0 ]; then echo "No zip ($ZIP_GLOB) in the main folder: nothing to do."; exit 0; fi

touches_workflows() { grep -qE '(^|/)\.github/workflows/' ; }

for z in "${zips[@]}"; do
  echo "== $z"
  tmp=$(mktemp -d)
  unzip -q "$z" -d "$tmp"
  mapfile -t patches < <(find "$tmp" -type f -name '*.patch' | sort)
  if [ ${#patches[@]} -gt 0 ]; then
    for p in "${patches[@]}"; do
      if git apply --numstat "$p" | cut -f3 | touches_workflows; then
        echo "::error::$p changes .github/workflows; GitHub does not let a workflow do that. Edit those files by hand."; exit 1
      fi
      if git apply --check "$p" 2>/dev/null; then
        echo "applying ${p#$tmp/}"; [ "${DRY_RUN:-0}" = 1 ] || git apply "$p"
      elif git apply --check -R "$p" 2>/dev/null; then
        echo "already applied: ${p#$tmp/}"
      else
        echo "::error::${p#$tmp/} does not apply to this repository. Check that it is the one the patch was made for."
        git apply --check "$p" || true
        exit 1
      fi
    done
  else
    root=$tmp
    entries=( "$tmp"/* "$tmp"/.[!.]* )
    # one wrapper folder (not .github, not a folder the repository already has) is stripped; else the zip's tree is
    # taken as is
    if [ ${#entries[@]} -eq 1 ] && [ -d "${entries[0]}" ]; then
      top=$(basename "${entries[0]}")
      if [ "$top" != ".github" ] && [ ! -e "$top" ]; then root=${entries[0]}; fi
    fi
    if [ -e "$root/.github/workflows" ]; then echo "::error::the zip holds .github/workflows; GitHub does not let a workflow change those. Not copied."; exit 1; fi
    echo "copying the zip's files:"; (cd "$root" && find . -type f | sed 's#^\./#  #')
    [ "${DRY_RUN:-0}" = 1 ] || cp -a "$root"/. .
  fi
  rm -rf "$tmp"
  if [ "${DRY_RUN:-0}" != 1 ] && [ "${KEEP_ZIP:-0}" != 1 ]; then git rm -q -f -- "$z" 2>/dev/null || rm -f -- "$z"; fi
done

[ "${DRY_RUN:-0}" = 1 ] && { echo "Dry run: nothing changed."; exit 0; }
git config user.name  >/dev/null || git config user.name  "github-actions[bot]"
git config user.email >/dev/null || git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
if git diff --cached --quiet; then echo "No changes to commit."; exit 0; fi
git commit -q -m "Apply ${zips[*]} (apply-zips.sh)"
[ "${NO_PUSH:-0}" = 1 ] || git push
echo "Done."
