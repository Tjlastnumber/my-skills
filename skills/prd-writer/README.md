# prd-writer

两阶段引导式 PRD 生成工具，产出可直接用于 vibe coding 的精确需求文档。

A guided PRD generation tool that produces precise requirements documents ready for vibe coding.

## 功能 / Features

- 三视角需求诊断（用户、管理层、技术）
- 概念版 PRD（≤ 200 字）快速对齐方向
- 范围冻结机制防止需求蔓延
- 落地版 PRD 覆盖页面结构、用户流程、文案规范、异常处理四大盲区

## 工作流程 / Workflow

1. **触发确认** — 复述核心需求，说明提问计划
2. **Phase 1：三视角诊断** — 3 轮提问收集用户/管理/技术视角信息
3. **Phase 2：概念版** — 输出 ≤200 字概念 PRD，与用户对齐方向
4. **Phase 3：范围冻结** — 确认后锁定范围，不再修改
5. **Phase 4：落地版** — 输出完整 PRD，四大盲区自检

## 目录结构 / Directory Layout

```
skills/prd-writer/
├── SKILL.md                    # Agent-facing workflow instructions
├── README.md                   # This file
├── templates/
│   ├── concept-prd.md          # Concept PRD template (≤200 words)
│   └── full-prd.md             # Full PRD structure + blind-spot checklist
└── examples/
    └── sample-concept.md       # Sample concept PRD output
```

## 使用方式 / Usage

本 skill 无脚本依赖，由 AI 助手在工作流中直接调用。向 AI 描述你的产品想法即可触发。
