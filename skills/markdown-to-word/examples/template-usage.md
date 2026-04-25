# Template Usage Example

This example shows how to invoke the skill directly with a built-in template and explicit CLI arguments.

## Inspect the academic template

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --show-template cn-thesis
```

## Normalize merged Markdown only

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --template cn-thesis --workdir /path/to/project --title-text "示例论文标题" --input-parts chapter-01.md chapter-02.md chapter-03.md --merged-output manuscript.md --normalized-output manuscript.normalized.md --normalize-markdown-only
```

## Generate rebuilt DOCX

```bash
python3 docs/superpowers/skills/markdown-to-word/scripts/markdown_to_word.py --template cn-thesis --workdir /path/to/project --title-text "示例论文标题" --input-parts chapter-01.md chapter-02.md chapter-03.md --merged-output manuscript.md --reference-doc outputs/reference.docx --output-docx outputs/final.docx
```

The `cn-thesis` template automatically applies thesis-oriented indentation, heading spacing, non-italic captions, and `（n）` ordered-list numbering.

Expected outputs:

- `outputs/reference.docx`
- `outputs/final.docx`
