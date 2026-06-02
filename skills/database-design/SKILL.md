---
name: database-design
description: 数据库设计规范与变更指南。当涉及新建表、修改列、新增枚举值、编写迁移脚本、设计新数据模块、或讨论表结构/列类型/索引/DDL等数据库相关话题时使用。即使用户没有明确说"数据库设计"，只要涉及表结构变更、字段设计、数据模型、迁移脚本，都应使用此 skill。
---

# 数据库设计规范

本数据库设计规范遵循一套统一的约定。当需要进行任何数据库结构变更时，请按照以下流程操作。

## 首要步骤：确认数据库方言

当用户需要编写 DDL 或迁移脚本时，**先询问用户使用哪种数据库方言**：

> "本项目支持 MySQL 和 PostgreSQL 两种方言。你当前使用的是哪种？"

后续所有 DDL 建议、迁移脚本仅针对用户选择的方言生成，不需要同时维护两份。

## 核心规则速查

以下规则适用于**所有**数据表，没有例外：

### 1. 表名

- 使用**项目前缀 + snake_case**（示例中用 `<prefix>_` 表示项目前缀）
- 单数名词：`<prefix>_project`、`<prefix>_document`、`<prefix>_user`
- 关联表用两个实体名拼接：`<prefix>_project_member`、`<prefix>_asset_reference`
- 详见：`references/naming-and-conventions.md`

### 2. 标准审计列（每张表必须包含）

每张表都包含以下 6 个标准列，不可省略：

| 列名 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `id` | VARCHAR(128) | NOT NULL | 主键，字符串雪花 ID |
| `create_time` | DATETIME / TIMESTAMP | CURRENT_TIMESTAMP | 创建时间 |
| `update_time` | DATETIME / TIMESTAMP | CURRENT_TIMESTAMP | 更新时间（MySQL 加 ON UPDATE） |
| `create_by` | VARCHAR(128) | NULL | 创建人 |
| `update_by` | VARCHAR(128) | NULL | 更新人 |
| `deleted_flag` | INT | 0 | 逻辑删除：0=正常，1=已删除 |

详见：`references/standard-columns.md`

### 3. 主键策略

- **所有主键均为 VARCHAR(128) 字符串**，不使用自增整数
- ID 由雪花算法生成，保证全局唯一和有序
- 详见：`references/standard-columns.md`

### 4. 无物理外键约束

- **所有表不在数据库中创建外键约束**
- 表之间的关系仅通过应用层逻辑维护
- 关联字段命名为 `<entity>_id`（如 `project_id`、`team_id`），并建立索引
- 详见：`references/domain-relationships.md`

### 5. 逻辑删除

- 使用 `deleted_flag INT DEFAULT 0` 实现软删除
- `0` = 正常记录，`1` = 已删除记录
- 所有查询默认只返回 `deleted_flag = 0` 的记录
- 详见：`references/standard-columns.md`

### 6. 枚举存储

枚举值在数据库中有三种存储方式，根据枚举类型选择：

| 策略 | 存储格式 | 适用场景 | 示例 |
|---|---|---|---|
| 字符串 code | VARCHAR | 业务语义明确的枚举 | `admin`、`active`、`text` |
| 整数 code | INT | 简单的二元/标志类型 | `0`(单次)、`1`(周期) |
| 枚举名 | VARCHAR | 状态流转类枚举 | `PUBLISHED`、`ARCHIVED` |

详见：`references/enum-and-type-strategy.md`

## 决策指引

根据你要做的事情，查阅对应的参考文档：

| 任务 | 参考文档 |
|---|---|
| 给表/列起名 | `references/naming-and-conventions.md` |
| 确认标准列和主键 | `references/standard-columns.md` |
| 选择枚举/JSON/布尔/时间类型 | `references/enum-and-type-strategy.md` |
| 写 DDL 或迁移脚本 | `references/ddl-and-migrations.md` |
| 理解表间关系建模 | `references/domain-relationships.md` |
| 新建表/列/枚举/迁移的完整流程 | `references/change-checklist.md` |

DDL 模板位于 `assets/ddl-templates/` 目录下，根据用户选择的方言使用对应模板。

## 禁止事项

- **禁止**使用数据库自增 ID
- **禁止**创建物理外键约束（FOREIGN KEY）
- **禁止**物理删除记录（DELETE），一律使用逻辑删除（`deleted_flag = 1`）
- **禁止**使用驼峰命名（数据库层一律 snake_case）
- **禁止**省略标准审计列
