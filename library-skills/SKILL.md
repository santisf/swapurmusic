---
name: library-skills
description: Use when starting work in a Python or JS/TS project to pull in up-to-date, official skills shipped by the project's installed libraries (FastAPI, Streamlit, and others). Keeps Claude's knowledge in sync with the actual installed library version, not its training cutoff. Run once per project, or after a dependency upgrade.
allowed-tools: Bash(uvx library-skills:*), Bash(npx library-skills:*), Bash(ls:*)
---

# library-skills

`tiangolo/library-skills` scans the current project's installed dependencies and pulls in any **official agent skills** the libraries ship with themselves. Skills are written into `.claude/skills/` (with `--claude`) or `.agents/` (default), as symlinks back into the installed packages, so they update automatically when you bump the library.

## When to use

- Starting a new feature in a Python or JS/TS project that depends on libraries known to ship skills (FastAPI, Streamlit, growing list at https://agentskills.io).
- Hitting a bug where Claude is using **deprecated patterns** for a library — pulling the library's own skill in fixes that immediately.
- Before any non-trivial work in an unfamiliar library, run this once to see if the author shipped guidance.

Skip if: the project has no installed dependencies (plain scratch dir), or you're already fluent in the library's current API.

## Run

Python project:

```bash
uvx library-skills --claude
```

JavaScript / TypeScript project:

```bash
npx library-skills --claude
```

The CLI scans installed deps, asks which skills to install, and writes symlinks under `.claude/skills/`. **Pass `--claude`** — without it, skills go to `.agents/`, which Claude Code does not auto-load.

## After installing

Skills are picked up on the next Claude Code session restart. Verify:

```bash
ls .claude/skills/
```

## Reference

- Repo: https://github.com/tiangolo/library-skills
- Docs: https://library-skills.io
- Index of libraries publishing skills: https://agentskills.io
