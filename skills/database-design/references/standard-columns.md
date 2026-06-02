# 标准列与主键策略

## 标准审计列

**每一张表**都必须包含以下 6 个标准列。这些列由应用层自动填充和维护，业务代码一般不需要直接操作它们。

### 列定义

| 列名 | MySQL 类型 | PostgreSQL 类型 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | VARCHAR(128) NOT NULL | VARCHAR(128) NOT NULL | — | 主键，雪花 ID |
| `create_time` | DATETIME | TIMESTAMP | CURRENT_TIMESTAMP | 记录创建时间 |
| `update_time` | DATETIME | TIMESTAMP | CURRENT_TIMESTAMP | 记录最后更新时间 |
| `create_by` | VARCHAR(128) | VARCHAR(128) | NULL | 创建人标识（用户 ID） |
| `update_by` | VARCHAR(128) | VARCHAR(128) | NULL | 最后更新人标识 |
| `deleted_flag` | INT | INT | 0 | 逻辑删除标识 |

### MySQL 特殊处理

MySQL 的 `update_time` 列使用 `ON UPDATE CURRENT_TIMESTAMP` 自动刷新：

```sql
update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

### PostgreSQL 处理

PostgreSQL 没有内建的 `ON UPDATE` 自动刷新机制，`update_time` 在应用层更新：

```sql
update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### 列顺序约定

在 DDL 中，标准列的排列顺序固定：

1. `id`（主键，放最前面）
2. 业务列（按逻辑分组排列）
3. `create_time`
4. `update_time`
5. `create_by`
6. `update_by`
7. `deleted_flag`（放最后）

## 主键策略

### ID 类型

所有表的主键均为 **VARCHAR(128)** 字符串类型。

**不使用**：
- 自增整数（AUTO_INCREMENT / SERIAL）
- UUID（个别遗留表除外）
- 复合主键

### ID 生成规则

ID 由雪花算法（Snowflake）生成，特点：
- 全局唯一
- 趋势递增（基于时间戳）
- 128 字符长度提供了充足的空间

在同一张表中，ID 生成方式应保持统一。新表一律使用雪花 ID。

### 主键命名

主键列名固定为 `id`，不使用 `xxx_id`（`xxx_id` 用于外键风格引用列）。

```
<prefix>_user.id              -- 主键
<prefix>_project_member.role_id -- 引用 <prefix>_role.id 的外键风格列
```

## 逻辑删除

### 机制

使用 `deleted_flag INT` 列实现软删除：

| 值 | 含义 |
|---|---|
| `0` | 正常记录（默认） |
| `1` | 已删除记录 |

### 规则

- **禁止物理删除**（DELETE 语句），所有删除操作一律通过 `UPDATE ... SET deleted_flag = 1` 实现
- 所有查询默认只返回 `deleted_flag = 0` 的记录
- 已删除的记录保留在数据库中，不参与业务查询但可审计追溯
- 即使业务上"删除"了一张表的所有关联数据，每条记录的 `deleted_flag` 都应被置为 1

### 列类型选择

`deleted_flag` 使用 **INT** 而非 BOOLEAN，原因：
- 保持 MySQL 和 PostgreSQL 两种方言下的类型一致性
- 与项目中其他 `_flag` 列（`readonly_flag`、`updated_flag`）类型一致
- INT 便于扩展（如未来需要 2=归档 等更多状态）

## 审计列填充规则

审计列的值由应用层自动填充，规则如下：

| 列 | INSERT 时 | UPDATE 时 |
|---|---|---|
| `create_time` | 自动填充当前时间 | 不变 |
| `update_time` | 自动填充当前时间 | 自动刷新为当前时间 |
| `create_by` | 自动填充当前用户 ID | 不变 |
| `update_by` | 自动填充当前用户 ID | 自动刷新为当前用户 ID |
| `deleted_flag` | 默认 0 | 仅在逻辑删除时置为 1 |

在 DDL 中，`create_time` 和 `update_time` 的数据库默认值为 `CURRENT_TIMESTAMP`，作为应用层填充失败时的兜底。
