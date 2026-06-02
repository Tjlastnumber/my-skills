# 变更检查清单

## 新建表

当需要创建一张新表时，按以下步骤执行：

### 1. 确认方言

询问用户使用的是 MySQL 还是 PostgreSQL。

### 2. 确定表名

- [ ] 使用项目前缀 + snake_case（`<prefix>_<entity>`）
- [ ] 使用单数名词
- [ ] 如果是关联表，考虑用 `<prefix>_<entity_a>_<entity_b>` 或业务语义命名
- [ ] 如果属于特定业务模块，考虑加模块前缀（如 `<prefix>_task_*`）

### 3. 确定列

- [ ] `id VARCHAR(128) NOT NULL`（主键，第一位）
- [ ] 业务列（按逻辑分组，参考 `enum-and-type-strategy.md` 选择类型）
- [ ] 所有外键风格列命名为 `<entity>_id`
- [ ] `create_time`（DATETIME / TIMESTAMP DEFAULT CURRENT_TIMESTAMP）
- [ ] `update_time`（DATETIME / TIMESTAMP，MySQL 加 ON UPDATE CURRENT_TIMESTAMP）
- [ ] `create_by VARCHAR(128) DEFAULT NULL`
- [ ] `update_by VARCHAR(128) DEFAULT NULL`
- [ ] `deleted_flag INT DEFAULT 0`

### 4. 确定索引

- [ ] 所有 `<entity>_id` 列建索引
- [ ] 经常作为查询条件的列建索引
- [ ] 索引命名：`idx_<table>_<col>`

### 5. 添加注释

- [ ] 表有注释
- [ ] 每个业务列有注释
- [ ] 标准审计列注释可省略

### 6. 编写 DDL

- [ ] 使用 `assets/ddl-templates/` 中对应方言的模板
- [ ] MySQL：包含 `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`
- [ ] PostgreSQL：使用 `COMMENT ON TABLE` / `COMMENT ON COLUMN`

### 7. 编写迁移脚本

- [ ] 文件名：`ddl_<dialect>_update_<YYYYMMDD>[_<feature>].sql`
- [ ] 存放于 `scripts/migrations/`（或团队约定的路径）
- [ ] 仅生成用户所选方言的一份

---

## 新增列

当需要在已有表中新增列时：

### 1. 确定列名和类型

- [ ] snake_case 命名
- [ ] 参考后缀约定（`_id`、`_at`、`_flag`、`_count`、`_json`、`_type`、`_status`）
- [ ] 根据用途选择类型（VARCHAR/INT/DATETIME/JSON 等，参考 `enum-and-type-strategy.md`）

### 2. 确定默认值

- [ ] 新增列**必须**有默认值或允许 NULL，避免历史数据报错
- [ ] 标志位列用 `INT DEFAULT 0`
- [ ] 文本列用 `DEFAULT NULL`
- [ ] 状态/类型列用合理的初始状态默认值

### 3. 编写迁移脚本

**MySQL**：
```sql
ALTER TABLE <prefix>_<table>
    ADD COLUMN <column> <type> DEFAULT <value> COMMENT '<注释>';
```

**PostgreSQL**：
```sql
ALTER TABLE <prefix>_<table>
    ADD COLUMN <column> <type> DEFAULT <value>;

COMMENT ON COLUMN <prefix>_<table>.<column> IS '<注释>';
```

### 4. 检查索引需求

- [ ] 如果是 `<entity>_id` 列，需要加索引
- [ ] 如果经常作为查询条件，考虑加索引

```sql
-- MySQL
ALTER TABLE <prefix>_<table> ADD INDEX idx_<table>_<col> (<col>);

-- PostgreSQL
CREATE INDEX idx_<table>_<col> ON <prefix>_<table> (<col>);
```

---

## 新增枚举值

当需要为已有的枚举列新增一个值时：

### 1. 确认存储策略

先确认该列使用的是哪种存储策略（参考 `enum-and-type-strategy.md`）：

- 字符串 code（如 `admin`、`active`）
- 整数 code（如 `0`、`1`）
- 枚举名（如 `PUBLISHED`、`ARCHIVED`）

### 2. 通常无需 DDL 变更

大多数枚举列是 VARCHAR 类型，新增枚举值只需要：
- [ ] 在应用层定义新的枚举常量
- [ ] 不需要修改数据库结构

### 3. 数据迁移（如需要）

如果需要将已有数据更新为新枚举值：

```sql
UPDATE <prefix>_<table>
SET <column> = '<new_value>'
WHERE <condition>;
```

---

## 新增索引

当需要为已有表添加索引时：

```sql
-- MySQL
ALTER TABLE <prefix>_<table> ADD INDEX idx_<table>_<col> (<col>);

-- PostgreSQL
CREATE INDEX idx_<table>_<col> ON <prefix>_<table> (<col>);
```

命名：`idx_<table>_<col(s)>`

---

## 编写迁移脚本的完整流程

1. **确认方言**（MySQL / PostgreSQL）
2. **命名文件**：`ddl_<dialect>_update_<YYYYMMDD>[_<feature>].sql`
3. **存放位置**：`scripts/migrations/`（或团队约定的路径）
4. **内容**：仅包含本次变更的 SQL（ALTER TABLE、CREATE INDEX 等）
5. **不包含**：外键约束、物理删除语句
6. **注释**：复杂变更加简要注释说明变更目的
