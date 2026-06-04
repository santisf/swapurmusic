---
name: library-skills
description: Use when starting work in a Python or JS/TS project to pull in up-to-date, official skills shipped by the project's installed libraries
allowed-tools: Bash(uvx library-skills:*), Bash(npx library-skills:*), Bash(ls:*)
---

# library-skills

`tiangolo/library-skills` scans the current project's installed dependencies and pulls in any **official agent skills** the libraries ship with themselves.

## When to use

- Starting a new feature in a Python or JS/TS project that depends on libraries known to ship skills
- Hitting a bug where Claude is using **deprecated patterns** for a library
- Before any non-trivial work in an unfamiliar library

## Run

Python project:
```bash
uvx library-skills --claude
```

JavaScript / TypeScript project:
```bash
npx library-skills --claude
```

## Reference

- Repo: https://github.com/tiangolo/library-skills
- Docs: https://library-skills.io
