---
name: markdown-to-word
description: Convert Markdown sources into DOCX/Word with a reusable template-driven pipeline.
context: user-invocable
argument-hint: "[--template=generic-default|cn-thesis] [--input-md=...] [--output-docx=...]"
---

# Markdown to Word

This skill provides a reusable `Markdown -> DOCX/Word` pipeline driven by built-in templates.

The skill bundles:

- a reusable Python converter script
- a built-in template registry
- template previews and sample Markdown files

## Template Selection

If the user has not specified a template, list the built-in templates first and ask them which one to use.

When listing templates, surface at least:

- language
- primary use cases
- whether `--title-text` is required
- Mermaid caption behavior

Current built-in templates:

- `generic-default`: general-purpose report / notes / document template
- `cn-thesis`: Chinese thesis-oriented template for academic manuscripts and dissertations, with thesis-style heading, caption, and numbering rules

List templates:

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
```

Show one template:

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --show-template cn-thesis
```

### Selection Prompt Template

When the user has not picked a template yet, ask with short option text like this:

```text
Choose a Markdown-to-Word template:
1. generic-default: general documents, reports, notes, no thesis-specific structure required
2. cn-thesis: Chinese thesis/manuscript formatting, stronger chapter/caption/reference rules, requires title text
```

If needed, add one short follow-up note:

```text
If you are converting a thesis or dissertation manuscript, choose cn-thesis. Otherwise choose generic-default.
```

## Bundled Resources

- `scripts/markdown_to_word.py`
- `templates/manifest.json`
- `templates/generic-default/`
- `templates/cn-thesis/`
- `requirements.txt`

Each template package includes:

- `template.json`: template config, including numbering, indentation, heading spacing, and caption spacing rules
- `preview.md`: human-readable summary
- `sample.md`: built-in sample Markdown input

The template manifest also carries selection metadata such as language, use cases, title-text requirement, Mermaid caption policy, and template-selection hints.

## `cn-thesis` Defaults

The `cn-thesis` template currently applies these defaults:

- body first-line indent: 2 Chinese characters
- Heading 1 spacing: 1.0 line before, 0.8 line after
- Heading 2-4 spacing: 0.5 line before, 0.5 line after
- heading font: `黑体`, not bold, black color
- ordered list numbering: `（1）`, `（2）`, `（3）` ...
- numbered lead-in content is split into a new paragraph instead of an inline line break
- figure/table captions are non-italic and use separately configurable figure/table spacing rules

## When To Use

- You need a repeatable `Markdown -> Word` flow.
- You want users to choose from multiple formatting templates.
- You want `pandoc` plus `python-docx` post-processing.
- You need optional Mermaid rendering, image wrapping normalization, or table cleanup.

## When Not To Use

- You only need to clean an existing DOCX without rebuilding from Markdown.
- You only need Markdown normalization and do not need Word output.
- You need a full publishing system beyond DOCX.

## Workflow

### Step 1: Choose a template

- If the user names a template, use it.
- If the user does not name a template, ask them to choose from the built-in templates.

### Step 2: Resolve inputs

The script supports:

- `--template`
- `--input-md`
- `--input-parts`
- `--title-text`
- `--merged-output`
- `--normalized-output`
- `--reference-doc`
- `--reference-template`
- `--output-docx`

### Step 3: Normalize Markdown if enabled

The pipeline can:

- normalize list spacing
- split collapsed starred items
- remove accidental indentation outside fenced code blocks
- split collapsed reference entries

### Step 4: Build or reuse reference DOCX

The pipeline either:

- copies `reference_template`, or
- builds a reference DOCX from the selected template's style config

### Step 5: Convert with Pandoc

```bash
pandoc <input.md> --reference-doc=<reference.docx> -o <output.docx>
```

### Step 6: Post-process DOCX

Depending on template and feature flags, the pipeline can:

- normalize heading / caption / code / reference styles
- apply template-specific heading spacing, first-line indentation, and heading fonts
- apply template-specific ordered-list numbering such as `（n）`
- split numbered lead-in content into separate paragraphs instead of inline line breaks
- keep figure and table captions non-italic, with independently configurable spacing
- split collapsed references inside DOCX
- replace Mermaid code blocks with images
- convert inline images to `wrapTopAndBottom`
- normalize table XML

## CLI Reference

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --help
```

Important options:

- `--list-templates`
- `--show-template <id>`
- `--template <id>`
- `--title-text <text>`
- `--normalize-markdown-only`
- `--normalized-output <path>`
- `--enable-mermaid`

## Examples

Use the generic template on a single Markdown file:

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --template generic-default --input-md docs/superpowers/skills/markdown-to-word/templates/generic-default/sample.md --reference-doc /tmp/generic-reference.docx --output-docx /tmp/generic-output.docx
```

Use the thesis template with generic multi-file manuscript inputs:

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --template cn-thesis --workdir /path/to/project --title-text "示例论文标题" --input-parts chapter-01.md chapter-02.md chapter-03.md --merged-output manuscript.md --reference-doc outputs/reference.docx --output-docx outputs/final.docx
```

This template automatically applies the `cn-thesis` indentation, heading spacing, heading font, caption, and numbered-list conventions.

Only normalize Markdown and write to a separate file:

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --template generic-default --input-md manuscript.md --normalized-output manuscript.normalized.md --normalize-markdown-only
```

## Failure Rules

- If no input Markdown can be resolved, stop immediately.
- If a template id is unknown, stop and list the available templates.
- If `pandoc` fails, abort the run.
- If Mermaid rendering fails, abort and surface stderr.
- If a Mermaid code block is missing an adjacent caption paragraph in templates that require caption pairing, abort rather than guessing.

## Verification

Minimum checks:

```bash
python3 -m py_compile docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --show-template generic-default
python3 -m json.tool docs/superpowers/skills/markdown-to-word/templates/manifest.json
```

## Prerequisites

Python packages:

- `python-docx`
- `lxml`

External tools:

- `pandoc`
- `npx` when Mermaid rendering is enabled
- `@mermaid-js/mermaid-cli@11.4.2` is pulled through `npx`
