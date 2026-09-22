# Instructions for AI coding agents (Codex, Claude, etc.)

This repo is a companion admin panel for a Metin2 Playerbots (Tieru, mt2009)
server, actively maintained by its operator with the help of AI coding
agents. Two rules apply regardless of which agent is working here:

## 1. Don't bump the version or touch CHANGELOG.md for small stuff

`VERSION` and a new `CHANGELOG.md` entry only get updated together, as one
bundled event, for a real batch of feature/fix work — never for a single
small tweak (an icon, a color, a spacing fix, a one-line bugfix). The
operator iterates fast, often every few minutes; flooding the version number
and changelog with that noise defeats the point of having them.

If you're not sure whether something is "significant enough" for a version
bump, ask the operator first instead of guessing either way.

## 2. Tag every CHANGELOG.md entry with which agent made it

End every `CHANGELOG.md` entry with an attribution badge on its own line,
right after the last bullet point (not in the entry's title/heading):

```
![via Claude](https://img.shields.io/badge/via-Claude-D97757)
```

or, if you are Codex:

```
![via Codex](https://img.shields.io/badge/via-Codex-10A37F)
```

This renders as an actual colored badge on GitHub, and the panel itself
parses this exact line (see `changelog_entries()` in `app.py`) to render a
small matching colored chip on `/changelog` — so keep the format (leading
`![via `, the name, then `](`) exactly as shown, or the panel won't pick it
up.

## Committing and pushing to GitHub

GitHub `origin/main` is the single source of truth when several agents work
on the panel. Before **every** change, first synchronise and verify the local
tree:

```sh
git fetch origin
git pull --ff-only origin main
git status --short --branch
```

Work only when that status is clean and the branch is aligned with
`origin/main`. If another agent pushed while work is in progress, stop before
deploying, pull the new commit, resolve or reapply the local change on top of
it, and verify the resulting diff.

Every completed change, including a small CSS or text fix, gets its own small,
focused commit and is pushed to `origin/main` immediately after validation.
This rule does **not** change the versioning rule above: small commits do not
bump `VERSION` or add a `CHANGELOG.md` entry. Deploy the exact pushed commit,
never an uncommitted VPS-only edit.

Never push to `TieruYT/metin2-playerbots` (the upstream engine this panel
sits next to) — that's not this repo's business at all.
