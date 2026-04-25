# markdown-to-word

将 Markdown 文稿转换为 DOCX/Word 的模板化技能包。

这个 skill 适合需要把 Markdown 内容整理为可交付 Word 文稿的场景，当前已经内置模板、脚本、示例和依赖说明，可以直接作为一个独立能力模块复用。

## Features

- 基于模板的 `Markdown -> DOCX/Word` 转换流程
- 内置 `generic-default` 与 `cn-thesis` 两套模板
- 基于 `pandoc + python-docx` 的后处理能力
- 支持 Markdown 归一化
- 支持可选 Mermaid 渲染
- 支持图片环绕与表格归一化处理

## Built-in Templates

| Template | Best For | Title Required | Mermaid Caption Policy |
| --- | --- | --- | --- |
| `generic-default` | 报告、方案、笔记、一般文档 | No | optional |
| `cn-thesis` | 中文论文、毕业设计说明书、学术主稿 | Yes | adjacent caption required |

模板预览文件：

- `templates/generic-default/preview.md`
- `templates/cn-thesis/preview.md`

## Prerequisites

Python 依赖：

```bash
pip install -r skills/markdown-to-word/requirements.txt
```

系统依赖：

- `pandoc`
- `npx`，当你需要 Mermaid 渲染时使用

## Quick Start

以下命令默认在仓库根目录执行。

1. 查看可用模板

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
```

2. 查看某个模板详情

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py --show-template cn-thesis
```

3. 使用通用模板转换单个 Markdown 文件

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py \
  --template generic-default \
  --input-md /path/to/input.md \
  --reference-doc /path/to/reference.docx \
  --output-docx /path/to/output.docx
```

4. 使用论文模板处理多文件主稿

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py \
  --template cn-thesis \
  --workdir /path/to/project \
  --title-text "示例论文标题" \
  --input-parts chapter-01.md chapter-02.md chapter-03.md \
  --merged-output manuscript.md \
  --reference-doc outputs/reference.docx \
  --output-docx outputs/final.docx
```

5. 只做 Markdown 归一化，不生成 DOCX

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py \
  --template generic-default \
  --input-md manuscript.md \
  --normalized-output manuscript.normalized.md \
  --normalize-markdown-only
```

## Project Layout

```text
skills/markdown-to-word/
├── README.md
├── SKILL.md
├── requirements.txt
├── examples/
│   └── template-usage.md
├── scripts/
│   └── markdown_to_word.py
└── templates/
    ├── manifest.json
    ├── cn-thesis/
    └── generic-default/
```

## Key Files

- `SKILL.md`：完整的 skill 说明、工作流、失败规则和校验方式
- `scripts/markdown_to_word.py`：主转换脚本
- `templates/manifest.json`：模板注册信息
- `examples/template-usage.md`：命令示例

## Verification

```bash
python3 -m py_compile skills/markdown-to-word/scripts/markdown_to_word.py
python3 skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
python3 skills/markdown-to-word/scripts/markdown_to_word.py --show-template generic-default
```

## Notes

- `cn-thesis` 默认带有更强的章节、题注、编号和论文样式约束
- 如果模板要求标题或 Mermaid 题注配对，缺失时应直接修正文稿而不是让脚本猜测
- 更详细的参数、失败规则和工作流，请查看 [`SKILL.md`](./SKILL.md)
