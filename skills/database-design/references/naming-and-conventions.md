# 命名规范

## 表命名

### 前缀

所有业务表使用**项目前缀**作为约定。前缀用于区分不同项目的表，避免命名冲突。本文档示例中使用 `<prefix>_` 作为占位符，实际使用时替换为项目自身的前缀。

### 基本规则

- **snake_case**：全小写，单词间用下划线分隔
- **单数名词**：`project`、`document`、`user`（不使用复数）
- **简洁明确**：名称应能准确表达实体的业务含义

**示例：**

| 表名 | 含义 |
|---|---|
| `<prefix>_project` | 项目 |
| `<prefix>_document` | 文档 |
| `<prefix>_instance` | 实例 |
| `<prefix>_notification` | 通知 |
| `<prefix>_task` | 任务 |

### 关联表命名

多对多或多对一的关联表，用两个实体名拼接：

| 关联表 | 关系 | 说明 |
|---|---|---|
| `<prefix>_project_member` | project ↔ user | 项目成员 |
| `<prefix>_team_member` | team ↔ user | 团队成员 |
| `<prefix>_asset_reference` | asset ↔ instance | 资产引用 |
| `<prefix>_template_reference` | template ↔ document | 模板引用 |

### 模块前缀

同一业务模块内的表使用模块名作为前缀的一部分，便于识别归属：

| 模块 | 表名示例 |
|---|---|
| 用户管理 | `<prefix>_user`、`<prefix>_role`、`<prefix>_team` |
| 项目管理 | `<prefix>_project`、`<prefix>_instance`、`<prefix>_document` |
| 资源模板 | `<prefix>_template`、`<prefix>_template_version`、`<prefix>_user_favorite` |
| 任务管理 | `<prefix>_task`、`<prefix>_task_submission`、`<prefix>_task_evaluation_record` |
| 通知 | `<prefix>_notification` |

---

## 列命名

### 基本规则

- **snake_case**：全小写，单词间用下划线分隔
- **简洁明确**：名称应能准确表达字段的业务含义

### 外键风格列

引用其他表的列命名为 `<被引用表>_id`：

| 列名 | 引用 | 说明 |
|---|---|---|
| `project_id` | `<prefix>_project.id` | 项目 ID |
| `team_id` | `<prefix>_team.id` | 团队 ID |
| `document_id` | `<prefix>_document.id` | 文档 ID |
| `image_id` | `<prefix>_image.id` | 镜像 ID |
| `instance_id` | `<prefix>_instance.id` | 实例 ID |
| `task_id` | `<prefix>_task.id` | 任务 ID |
| `submission_id` | `<prefix>_task_submission.id` | 提交 ID |

### 后缀约定

使用一致的列名后缀来表达特定的语义，便于快速理解列的用途：

| 后缀 | 语义 | 类型约定 | 示例 |
|---|---|---|---|
| `_id` | 外键引用 | VARCHAR(128) | `project_id`、`user_id` |
| `_at` | 时间点（事件发生时刻） | DATETIME / TIMESTAMP | `submitted_at`、`published_at`、`last_login_at` |
| `_time` | 时间点（同 `_at`，审计列使用此格式） | DATETIME / TIMESTAMP | `create_time`、`update_time`、`expire_time` |
| `_flag` | 标志位（0/1） | INT | `deleted_flag`、`readonly_flag`、`updated_flag` |
| `_enabled` | 启用状态 | INT / BOOLEAN | `notify_enabled`、`featured` |
| `_count` | 计数 | INT | `reference_count`、`favorite_count`、`submission_count` |
| `_json` | JSON 格式存储的复杂数据 | JSON / TEXT | `config_json`、`scores_json`、`snapshot_json` |
| `_name` | 名称 | VARCHAR | `user_name`、`nick_name`、`version_name` |
| `_no` | 编号 | VARCHAR / INT | `version_no`、`rank_no` |
| `_type` | 类型分类 | VARCHAR / INT | `priority_type`、`log_type`、`resource_type` |
| `_status` | 状态 | VARCHAR / INT | `status`、`validation_status` |

### 命名细节

- **时间列**：事件类时间用 `_at` 后缀（`submitted_at`、`evaluated_at`）；审计类时间用 `_time` 后缀（`create_time`、`update_time`）
- **布尔/标志**：统一使用 `_flag` 后缀 + INT 类型（0/1），不用 BOOLEAN 类型，以保持与 `deleted_flag` 的一致性
- **JSON 列**：结构化数据用原生 JSON 类型（MySQL）或 JSON/TEXT 类型（PostgreSQL），列名加 `_json` 后缀
- **状态列**：直接命名为 `status` 或 `<scope>_status`（如 `validation_status`），类型通常为 VARCHAR

### 列名避免

- **避免**使用数据库保留字（如 `order`、`group`、`key`），必要时加前缀消歧
- **避免**使用缩写（除非是团队广泛认可的缩写，如 `env`、`cfg`）
- **避免**在列名中重复表名（如在 `<prefix>_project` 表中使用 `project_name` 而不是 `name` 时，考虑是否可以用 `name`）
