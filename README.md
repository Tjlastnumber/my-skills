# my-skills

> A growing personal repository of reusable skills, workflows, templates, and automation utilities.

一个持续积累的个人 skills 库。

这里沉淀的不是零散提示词，而是可以长期复用的能力模块：说明文档、脚本、模板、示例、依赖和约束会尽量放在一起维护，让每个 skill 都更容易理解、复用和演进。

## What This Repo Is

这个仓库主要用来整理我在日常工作流里不断沉淀下来的 skills，包括但不限于：

- AI 助手可调用的结构化能力模块
- 可重复执行的自动化流程
- 面向具体场景的脚本与模板组合
- 能长期维护的个人知识资产

目标不是堆积零碎工具，而是把常用能力做成真正可复用的 skill package。

## Current Skills

目前仓库里已经整理出的 skill：

| Skill | Purpose | Highlights | Status |
| --- | --- | --- | --- |
| [`markdown-to-word`](skills/markdown-to-word/README.md) | 将 Markdown 文稿转换为 DOCX/Word | 内置 `generic-default`、`cn-thesis` 模板，支持 `pandoc + python-docx` 后处理、Markdown 归一化、可选 Mermaid 渲染 | available |

## Featured Skill

### `markdown-to-word`

一个偏实用型的文档处理 skill，用于把 Markdown 内容整理成可交付的 Word 文稿。

文档入口：[skills/markdown-to-word/README.md](skills/markdown-to-word/README.md)

当前已具备：

- 基于模板的 `Markdown -> DOCX/Word` 转换流程
- 内置 `generic-default` 与 `cn-thesis` 两类模板
- 支持 `pandoc + python-docx` 的后处理能力
- 支持 Markdown 归一化、表格归一化、图片处理
- 支持可选 Mermaid 渲染

模板定位：

- `generic-default`：适合报告、方案、笔记、一般文档
- `cn-thesis`：适合中文论文、毕业设计说明书、学术主稿等场景

## Quick Start

以 `markdown-to-word` 为例：

1. 安装 Python 依赖

```bash
pip install -r skills/markdown-to-word/requirements.txt
```

2. 查看可用模板

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py --list-templates
```

3. 查看某个模板的详情

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py --show-template cn-thesis
```

4. 执行 Markdown 转 Word

```bash
python3 skills/markdown-to-word/scripts/markdown_to_word.py \
  --template generic-default \
  --input-md /path/to/input.md \
  --reference-doc /path/to/reference.docx \
  --output-docx /path/to/output.docx
```

额外说明：

- 本地需要安装 `pandoc`
- 如果启用 Mermaid 渲染，还需要可用的 `npx`

## Repository Layout

```text
.
├── README.md
└── skills/
    └── markdown-to-word/
        ├── SKILL.md
        ├── requirements.txt
        ├── examples/
        ├── scripts/
        └── templates/
```

## Skill Conventions

这个仓库后续新增 skill 时，默认会尽量遵守下面的组织方式：

- `SKILL.md`：说明这个 skill 做什么、何时使用、如何使用
- `scripts/`：可执行脚本或工具实现
- `templates/`：模板、配置、样例输入、静态资源
- `examples/`：典型调用方式或最小使用示例
- `requirements.txt`：该 skill 的 Python 依赖

设计原则：

- 自包含：文档、脚本、模板尽量放在一个目录内闭环
- 可复用：优先沉淀能多次重复使用的能力
- 可验证：尽量提供最小可运行示例或校验方式
- 可演进：允许后续持续补模板、脚本和规则

## Why This Repo

这个仓库更像一个不断生长的个人能力仓库，而不是单次项目代码集合。

它适合用来参考这些问题：

- 如何把一个能力封装成长期可维护的 skill
- 如何把脚本、模板、说明文档、示例放在一起维护
- 如何把个人经验逐步沉淀成稳定资产

## Roadmap

后续会继续把更多个人 skills 整理进来，方向包括：

- 文档处理与格式转换
- 写作与排版辅助
- 工程自动化脚本
- 开发流程中的常用工作流封装
- 更适合 AI 助手直接调用的结构化能力模块

## Maintenance

后续新增 skill 时，原则上会按这个顺序整理：

1. 明确 skill 的适用场景和边界
2. 补齐 `SKILL.md`
3. 补齐脚本、模板、示例和依赖
4. 更新根目录 `README.md`

这样可以尽量保证整个仓库始终保持可浏览、可理解、可直接上手。

## How To Add A New Skill

新增一个 skill 时，建议直接按下面的最小结构开始：

```text
skills/
  your-skill-name/
    README.md
    SKILL.md
    requirements.txt
    scripts/
    templates/
    examples/
```

建议步骤：

1. 先确定 skill 名称，尽量使用清晰的 kebab-case，例如 `markdown-to-word`
2. 在 `SKILL.md` 里写清楚用途、适用场景、输入参数、工作流、失败规则和校验方式
3. 在 `README.md` 里写给仓库访问者看的公开说明，重点放在功能、快速开始和目录结构
4. 把脚本放进 `scripts/`，把模板或配置放进 `templates/`，把示例放进 `examples/`
5. 如果有 Python 依赖，补 `requirements.txt`
6. 最后把这个 skill 收录到根目录 `README.md` 的 `Current Skills` 中

最小检查清单：

- 目录名和 skill 名称一致
- `README.md` 和 `SKILL.md` 的定位清晰，不相互重复
- 至少有一个可运行示例或验证命令
- 根目录 `README.md` 已加入入口链接
- 路径说明基于仓库当前真实结构

## License

This repository is licensed under the MIT License.
