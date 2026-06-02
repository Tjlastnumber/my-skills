# 领域关系建模

## 核心原则：无物理外键

**所有表不在数据库中创建外键约束（FOREIGN KEY）。**

这是硬性约定。表之间的关系完全由应用层（业务代码）来维护和校验。

### 为什么不用外键

- **性能**：外键约束在写入和删除时带来额外校验开销
- **灵活性**：便于数据迁移、批量导入/导出、分库分表
- **部署**：微服务架构下，不同模块可能使用不同的数据库实例
- **运维**：避免因外键导致的锁表、级联问题

### 替代方案

虽然没有物理外键，但通过以下手段保证数据一致性：

1. **命名约定**：引用列统一命名为 `<entity>_id`，明确表达关系意图
2. **索引**：在所有外键风格列上建立索引，保证关联查询性能
3. **应用层校验**：在业务代码中校验关联数据的存在性和有效性
4. **逻辑删除**：不物理删除记录，避免引用数据消失的问题

---

## 关系建模模式

### 一对多（1:N）

在"多"方表中添加 `<one_entity>_id` 列：

```
<prefix>_project (1) ──< <prefix>_instance (N)
    instance.project_id → project.id

<prefix>_project (1) ──< <prefix>_document (N)
    document.project_id → project.id

<prefix>_document (1) ──< <prefix>_document_version (N)
    document_version.document_id → document.id

<prefix>_document_version (1) ──< <prefix>_document_version_attachment (N)
    document_version_attachment.version_id → document_version.id

<prefix>_task (1) ──< <prefix>_task_submission (N)
    task_submission.task_id → task.id
```

DDL 中只加列和索引，不加外键约束：

```sql
CREATE TABLE <prefix>_instance (
    id          VARCHAR(128) NOT NULL,
    project_id  VARCHAR(128) DEFAULT NULL,
    ...
    PRIMARY KEY (id),
    INDEX idx_instance_project_id (project_id)
);
```

### 多对多（M:N）

使用独立的关联表，包含双方的 `_id` 引用列：

```
<prefix>_project (M) ──< <prefix>_project_member >── (N) <prefix>_user
    project_member.project_id → project.id
    project_member.user_id    → user.id

<prefix>_team (M) ──< <prefix>_team_member >── (N) <prefix>_user
    team_member.team_id  → team.id
    team_member.user_id  → user.id

<prefix>_asset (M) ──< <prefix>_asset_reference >── (N) <prefix>_instance
    asset_reference.asset_id    → asset.id
    asset_reference.instance_id → instance.id
```

关联表本身也是一张标准的业务表，包含完整的标准审计列（`id`、`create_time`、`update_time`、`create_by`、`update_by`、`deleted_flag`）。

### 多态引用

当一张表需要引用不同类型的目标表时，使用 `resource_type` + `resource_id` 的组合：

```
<prefix>_user_favorite
    resource_type  VARCHAR(64)  -- 目标类型: 'TEMPLATE'、'DOCUMENT' 等
    resource_id    VARCHAR(128) -- 目标表的 id
```

这种模式下，`resource_id` 不指向固定的表，需要应用层根据 `resource_type` 路由到正确的表。

---

## 聚合与模块边界

### 领域模块示例

项目可按业务领域划分为多个模块，每个模块管理自己的表。以下为示例划分：

| 领域模块 | 核心表 | 说明 |
|---|---|---|
| 用户管理 | `user`、`role`、`team`、`team_member` | 账户、角色与团队 |
| 项目管理 | `project`、`project_member`、`instance`、`image`、`document`、`document_version`、`attachment`、`asset`、`asset_reference` | 项目核心业务 |
| 资源模板 | `template`、`template_version`、`template_version_attachment`、`template_reference`、`user_favorite` | 可复用的共享资源 |
| 任务管理 | `task`、`task_submission`、`task_evaluation_record` | 任务/工单流程 |
| 通知 | `notification` | 站内通知 |

（以上表名均省略了 `<prefix>_` 前缀）

### 跨模块引用

当不同模块的表之间需要关联时，仍然通过 `<entity>_id` 列引用，不在数据库层创建外键：

```
<prefix>_task_dataset_mount
    project_id              → <prefix>_project.id（项目管理模块）
    source_document_id      → <prefix>_document.id（项目管理模块）
    source_document_version_id → <prefix>_document_version.id（项目管理模块）

<prefix>_template
    source_project_id       → <prefix>_project.id（项目管理模块）
    source_document_id      → <prefix>_document.id（项目管理模块）
```

跨模块引用时，在列名上加业务前缀可以消除歧义：
- `source_project_id`（来源项目）
- `source_document_id`（来源文档）
- `target_project_id`（目标项目）
- `target_document_id`（目标文档）

---

## 版本化模式

当业务需要追踪数据的变更历史时，可使用"版本"模式：

### 模式结构

```
主表 (1) ──< 版本表 (N) ──< 版本附件表 (N)
```

| 主表 | 版本表 | 附件表 |
|---|---|---|
| `<prefix>_document` | `<prefix>_document_version` | `<prefix>_document_version_attachment` |
| `<prefix>_template` | `<prefix>_template_version` | `<prefix>_template_version_attachment` |

### 版本表的共同特征

- `version_no`（INT）：版本号，递增整数
- `version_name`（VARCHAR）：版本显示名（如 "v1"、"v2"）
- `version_note`（TEXT）：版本说明
- 主表通过 `current_version_id`/`current_version_no` 和 `latest_version_id`/`latest_version_no` 追踪当前和最新版本

---

## 快照/副本模式

某些场景下需要将数据"快照"到另一张表中，作为历史记录：

```
<prefix>_attachment (主表)
    ↓ 快照复制
<prefix>_document_version_attachment (版本附件快照)
<prefix>_template_version_attachment (模板版本附件快照)
```

快照表复制了主表的关键字段（`filename`、`file_size`、`file_type`、`file_md5`、`bucket_name`、`object_name`），并通过 `source_attachment_id` 引用原始附件。

这种模式用于确保版本数据不受主表数据变更的影响。
