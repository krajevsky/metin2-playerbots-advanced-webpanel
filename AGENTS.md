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

Every time `VERSION` does get bumped, also create and push a matching
annotated git tag (`v<version>`, e.g. `v1.60.0`) once the commit is on
`origin/main`:

```sh
git tag -a v1.60.0 -m "1.60.0: <short summary>. Full notes: CHANGELOG.md"
git push origin v1.60.0
```

This is deliberately just a tag, not a full GitHub Release (that would need
a Personal Access Token neither agent holds — operator's choice, 2026-09-22).
A tag alone is enough for GitHub to offer "create a release from this tag"
whenever the operator wants a formal release page; the tag message can be
pasted straight in as release notes.

## 2. Tag every CHANGELOG.md entry with which agent made it

End every `CHANGELOG.md` entry with an attribution badge on its own line,
right after the last bullet point (not in the entry's title/heading). Work
done with AI assistance (that's you) is credited jointly with the operator,
`Seban` — the badge text is `<Agent> by Seban`:

```
![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)
```

or, if you are Codex:

```
![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
```

**Exception: Tieru.** As of 2026-09-22 the operator merged Tieru's own
classic panel work into this same codebase instead of maintaining two
panels separately (see repo README for the current shape). Any change that
is actually Tieru's own code being brought in directly — not something
written with AI assistance — gets credited to him alone, no "by Seban" half:

```
![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)
```

This renders as an actual colored badge on GitHub, and the panel itself
parses this exact line (see `changelog_entries()` in `app.py`) to render a
small matching colored chip on `/changelog` — the `by <name>` half additionally
gets an animated rainbow-gradient + twinkling star (`.via-rainbow`/`.via-star`
in `static/enhancements.css`) there, though GitHub's own badge obviously can't
animate. Keep the format (leading `![via `, the name, then `](`) exactly as
shown, or the panel won't pick it up.

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

## VPS environment and deployment

The production VPS runs only the MT2009 r41023 / Playerbots 2.x line. Its
active game checkout is `/opt/metin2-mt2009/mt2009-r41023-base`; Docker Compose
lives in `/opt/metin2-mt2009/mt2009-r41023-base/linux-port/docker`.

The custom Seban Panel served on port 7790 is checked out at
`/opt/seban-panel-custom`. Deploy a pushed `origin/main` commit with:

```sh
git -C /opt/seban-panel-custom fetch origin main
git -C /opt/seban-panel-custom merge --ff-only FETCH_HEAD
cd /opt/metin2-mt2009/mt2009-r41023-base/linux-port/docker
sudo -n docker compose up -d --build --no-deps seban-panel seban-collector seban-item-grants
```

Use `sudo -n` only for the explicitly required service and deployment work.
Preserve the `account`, `common`, `player`, and `log` databases, the custom
panel, `seban-overrides`, the `seban-updater` service, and overrides for
Skrzynia Ucznia, Szkatułka Blasku Księżyca, and demonstration characters.
Never remove player data, bots, databases, or directories without an explicit
operator request and a verified backup. Never use r40250 or Playerbots 1.x.
