# AGENTS.md

## Repository

Personal collection of reusable skill packages. Each skill is self-contained under `skills/<name>/`.

## Structure

Each skill directory must contain:
- `SKILL.md` — agent-facing instructions (what, when, how, failure rules)
- `README.md` — human-facing overview
- `scripts/` — executable tooling
- `templates/` — configs, static assets, sample inputs
- `examples/` — usage examples
- `requirements.txt` — Python deps (if any)

## Adding a New Skill

1. Create `skills/<kebab-case-name>/` with the structure above
2. Write `SKILL.md` first (purpose, workflow, failure rules, verification)
3. Add scripts, templates, examples, and `requirements.txt`
4. Add an entry to the root `README.md` Current Skills table

## Existing Skill: `markdown-to-word`

Python-based `Markdown -> DOCX` pipeline using `pandoc` + `python-docx`.

**Dependencies:** `pip install -r skills/markdown-to-word/requirements.txt` (needs `python-docx`, `lxml`). System must have `pandoc` installed. Mermaid rendering requires `npx`.

**Run:**
```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
python3 skills/markdown-to-word/scripts/markdown_to_word.py --template <id> --input-md <path> --output-docx <path>
```

**Verify:**
```bash
python3 -m py_compile skills/markdown-to-word/scripts/markdown_to_word.py
python3 -m json.tool skills/markdown-to-word/templates/manifest.json
```

**Path note:** SKILL.md examples reference `docs/superpowers/skills/...` paths from a different deployment context. Actual repo paths are `skills/...`.

## Conventions

- Skill names use kebab-case
- No test suite or CI configured — verify with `py_compile` and `--list-templates`
- Bilingual repo: README is Chinese/English; keep both audiences in mind
