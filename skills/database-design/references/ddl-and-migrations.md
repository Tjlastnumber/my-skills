# DDL 与迁移脚本

## 数据库方言

本规范支持两种数据库：**MySQL** 和 **PostgreSQL**。

当需要编写 DDL 或迁移脚本时，**先确认用户使用的数据库方言**，然后仅生成该方言的脚本，不需要同时维护两份。

### 方言差异对照

供参考，当用户需要将 DDL 从一种方言转换为另一种时使用：

| 特性 | MySQL | PostgreSQL |
|---|---|---|
| 时间类型 | `DATETIME DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` |
| 自动更新时间 | `ON UPDATE CURRENT_TIMESTAMP` | 无内建支持，应用层处理 |
| 布尔/标志 | `INT DEFAULT 0` | `INT DEFAULT 0`（保持一致）或 `BOOLEAN DEFAULT FALSE` |
| JSON 类型 | `JSON` | `JSON` 或 `JSONB` |
| 长文本 | `MEDIUMTEXT` / `TEXT` | `TEXT` |
| 表选项 | `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4` | 无（PostgreSQL 无存储引擎概念） |
| 列注释 | `COMMENT '注释'`（跟在列定义后） | `COMMENT ON COLUMN table.col IS '注释'`（独立语句） |
| 表注释 | `COMMENT='注释'`（在表选项中） | `COMMENT ON TABLE table IS '注释'`（独立语句） |
| 索引创建 | 在 CREATE TABLE 内定义 | 在 CREATE TABLE 内或 `CREATE INDEX` |
| 自增 | `AUTO_INCREMENT` | `SERIAL` / `GENERATED ALWAYS AS IDENTITY` |

实际差异处理建议：
- `deleted_flag` 在两种方言中都使用 `INT DEFAULT 0`（不用 BOOLEAN）
- `_flag` 类型列在 MySQL 中可用 `TINYINT(1)` 或 `INT`，PostgreSQL 中使用 `INT`
- 时间列在 MySQL 中用 `DATETIME`，PostgreSQL 中用 `TIMESTAMP`

---

## DDL 规范

### 建表语句结构

建表语句按以下顺序组织：

1. `CREATE TABLE` 语句
2. `id` 主键列（第一位）
3. 业务列（按逻辑分组排列）
4. 标准审计列（`create_time` → `update_time` → `create_by` → `update_by` → `deleted_flag`）
5. 主键约束 `PRIMARY KEY (id)`
6. 索引定义
7. 表选项（MySQL 的 ENGINE/CHARSET）
8. 表/列注释

DDL 模板见 `assets/ddl-templates/` 目录。

### 索引规范

**命名**：`idx_<table_name>_<column(s)>`

```sql
-- MySQL（在建表语句内）
INDEX idx_project_team_id (team_id),
INDEX idx_instance_project_id (project_id)

-- PostgreSQL（独立语句或建表语句内）
CREATE INDEX idx_project_team_id ON <prefix>_project (team_id);
CREATE INDEX idx_instance_project_id ON <prefix>_instance (project_id);
```

**何时建索引**：
- 所有外键风格列（`<entity>_id`）都应建索引
- 经常作为查询条件的列
- 经常用于排序的列
- **不建**唯一索引来模拟唯一约束（除非业务确实需要，如 `user.email` 或 `user.user_name`）

### 注释规范

每张表和每个业务列都应有注释。标准审计列的注释可以省略（因为语义固定）。

**MySQL**：
```sql
CREATE TABLE <prefix>_xxx (
    id           VARCHAR(128) NOT NULL COMMENT '主键ID',
    name         VARCHAR(255) NOT NULL COMMENT '名称',
    project_id   VARCHAR(128) DEFAULT NULL COMMENT '关联项目ID',
    ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务表说明';
```

**PostgreSQL**：
```sql
CREATE TABLE <prefix>_xxx (
    id          VARCHAR(128) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    project_id  VARCHAR(128) DEFAULT NULL,
    ...
);

COMMENT ON TABLE <prefix>_xxx IS '业务表说明';
COMMENT ON COLUMN <prefix>_xxx.id IS '主键ID';
COMMENT ON COLUMN <prefix>_xxx.name IS '名称';
COMMENT ON COLUMN <prefix>_xxx.project_id IS '关联项目ID';
```

---

## 迁移脚本规范

### 命名格式

```
ddl_<dialect>_update_<YYYYMMDD>[_<feature>].sql
```

| 部分 | 说明 |
|---|---|
| `<dialect>` | `mysql` 或 `postgresql` |
| `<YYYYMMDD>` | 脚本创建日期 |
| `<feature>` | 可选，简短的功能描述 |

**示例**：
```
ddl_mysql_update_20260310.sql
ddl_postgresql_update_20260310.sql
ddl_mysql_update_20260408_task_module.sql
ddl_postgresql_update_20260408_task_module.sql
ddl_mysql_update_20260407_document_version.sql
ddl_postgresql_update_20260407_document_version.sql
```

### 存放位置

迁移脚本存放在项目的 `scripts/migrations/` 目录下（或按团队约定的统一路径）。

### 脚本内容规范

每个迁移脚本应：
1. **自包含**：可以在基线之上独立执行
2. **幂等性**（推荐）：使用 `IF NOT EXISTS`（MySQL 8+/PostgreSQL）或 `IF EXISTS` 判断
3. **按日期顺序执行**：文件名中的日期决定了执行顺序

### 新增列示例

**MySQL**：
```sql
ALTER TABLE <prefix>_template
    ADD COLUMN featured INT DEFAULT 0 COMMENT '精选标识: 0=否, 1=是';
```

**PostgreSQL**：
```sql
ALTER TABLE <prefix>_template
    ADD COLUMN featured INT DEFAULT 0;

COMMENT ON COLUMN <prefix>_template.featured IS '精选标识: 0=否, 1=是';
```

### 新增表示例

参见 `assets/ddl-templates/` 中的模板文件。

### 修改列类型

**MySQL**：
```sql
ALTER TABLE <prefix>_task
    MODIFY COLUMN source_project_id VARCHAR(128) DEFAULT NULL COMMENT '来源项目ID';
```

**PostgreSQL**：
```sql
ALTER TABLE <prefix>_task
    ALTER COLUMN source_project_id TYPE VARCHAR(128),
    ALTER COLUMN source_project_id SET DEFAULT NULL;

COMMENT ON COLUMN <prefix>_task.source_project_id IS '来源项目ID';
```

### 注意事项

- 迁移脚本中**不创建外键约束**
- 新增列时**总是指定默认值**（或允许 NULL），避免历史数据出错
- 新增非空列时，先用默认值填充历史数据，再视业务需要决定是否收紧约束
- `deleted_flag` 列**不能遗漏**，任何新表都必须包含
