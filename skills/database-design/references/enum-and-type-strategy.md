# 枚举与类型策略

## 枚举存储策略

枚举值在数据库中有三种存储方式。选择哪种取决于枚举的业务特征。

### 策略一：字符串 code（推荐，最常用）

将业务语义明确的字符串直接存入数据库。

**适用场景**：
- 枚举值有明确的业务含义
- 值的数量固定且有限
- 查询时经常需要按枚举值过滤

**示例**：

| 列 | 类型 | 存储值 | 业务含义 |
|---|---|---|---|
| `role` | VARCHAR(64) | `admin`、`user` | 用户角色 |
| `status` | VARCHAR(128) | `pending`、`active` | 用户状态 |
| `role` | VARCHAR(32) | `owner`、`admin`、`viewer` | 项目成员角色 |
| `type` | VARCHAR(64) | `text`、`image`、`video` | 文档类型 |
| `type` | VARCHAR(64) | `plugin`、`theme`、`extension` | 资产类型 |

**优点**：
- 数据库直接可读，查数据时无需查码表
- 新增枚举值不需要改数据库结构
- 与 API 响应/请求格式一致

**列宽建议**：VARCHAR(32) ~ VARCHAR(128)，留出扩展空间。

### 策略二：整数 code

将枚举映射为整数存入数据库。

**适用场景**：
- 简单的二元/三元标志
- 性能敏感场景（整数比较更快）
- 与外部系统对接时已约定整数编码

**示例**：

| 列 | 类型 | 存储值 | 业务含义 |
|---|---|---|---|
| `type` | INT | `0` = 单次, `1` = 周期 | 实例运行类型 |
| `deleted_flag` | INT | `0` = 正常, `1` = 已删除 | 逻辑删除标识 |

**注意**：整数 code 的可读性差，仅在简单标志或特殊性能需求时使用。新枚举优先选择字符串 code。

### 策略三：枚举名（大写常量名）

将枚举的常量名（大写）直接存入数据库。

**适用场景**：
- 状态流转类枚举（状态机）
- 枚举值与代码中的常量名一一对应
- 值的集合可能扩展

**示例**：

| 列 | 类型 | 存储值 | 业务含义 |
|---|---|---|---|
| `status` | VARCHAR(32) | `DRAFT`、`REVIEW`、`ACTIVE`、`COMPLETED`、`ARCHIVED` | 任务生命周期状态 |
| `status` | VARCHAR(32) | `PUBLISHED`、`ARCHIVED` | 模板发布状态 |
| `validation_status` | VARCHAR(32) | `PENDING`、`PASSED`、`FAILED` | 提交验证状态 |
| `status` | VARCHAR(20) | `UNREAD`、`READ` | 通知阅读状态 |
| `priority_type` | VARCHAR(32) | `BASIC`、`ADVANCED` | 优先级类型 |
| `log_type` | VARCHAR(32) | `REALTIME`、`ARCHIVE` | 日志类型 |
| `rsvp_status` | VARCHAR(32) | `CONFIRMED`、`CANCELLED` | 报名状态 |

### 选择决策

```
枚举是否只有 0/1 或简单的二元标志？
  → 是：用整数 code（策略二）
  → 否：继续

枚举是否是状态流转（状态机），值用大写常量更自然？
  → 是：用枚举名（策略三）
  → 否：用字符串 code（策略一）
```

---

## JSON 列

### 使用场景

当字段存储的是结构化的复合数据（对象/数组），且：
- 结构可能变化
- 不需要按内部字段做数据库查询过滤
- 整体读写为主

### 列类型

| 数据库 | 类型 | 说明 |
|---|---|---|
| MySQL | `JSON` | 原生 JSON 类型，有校验和高效解析 |
| PostgreSQL | `JSON` 或 `JSONB` | JSONB 存储为二进制，查询更快但写入稍慢 |

对于大段 JSON 文本，也可以用 `TEXT` 类型存储（列名加 `_json` 后缀）。

### 示例

| 列名 | 类型 | 存储内容 |
|---|---|---|
| `labels` | JSON | 标签数组 |
| `tags` | JSON | 标签数组 |
| `profile` | JSON | 配置对象 |
| `config_json` | TEXT | 扩展配置（JSON 字符串） |
| `scores_json` | TEXT | 评分明细（JSON 字符串） |
| `snapshot_json` | TEXT | 快照数据（JSON 字符串） |

### 设计原则

- 短命名（`labels`、`tags`、`profile`）可用原生 JSON 类型
- 长命名或大段文本用 `TEXT` 类型 + `_json` 后缀
- **避免**将需要频繁独立查询的字段放入 JSON 中——应拆成独立列并建索引

---

## 布尔类型

### 统一使用 INT 而非 BOOLEAN

标志位列统一使用 **INT** 类型（0/1），不使用 BOOLEAN：

| 列 | 类型 | 说明 |
|---|---|---|
| `deleted_flag` | INT DEFAULT 0 | 0=正常, 1=删除 |
| `readonly_flag` | INT DEFAULT 0 | 0=可写, 1=只读 |
| `updated_flag` | INT DEFAULT 0 | 0=未更新, 1=已更新 |
| `notify_enabled` | INT DEFAULT 1 | 0=关闭, 1=开启 |

原因：
- 保持 MySQL 和 PostgreSQL 双方言兼容
- 与项目中 `_flag` 列的类型保持一致
- INT 便于扩展更多状态值

---

## 时间类型

| 数据库 | 类型 | 说明 |
|---|---|---|
| MySQL | `DATETIME` | 范围广（1000-9999年），不随时区变化 |
| PostgreSQL | `TIMESTAMP` | 等价于 MySQL 的 DATETIME |

**不使用** `TIMESTAMP WITH TIME ZONE`（PostgreSQL）或 `TIMESTAMP`（MySQL 的窄范围版本），统一使用无时区的 DATETIME / TIMESTAMP，时区在应用层处理。

### 特殊时间列

- 截止时间/过期时间：`expire_time`、`deadline_time`、`end_time`
- 事件时间点：用 `_at` 后缀（`submitted_at`、`published_at`、`evaluated_at`）

---

## 文本类型选择

| 场景 | MySQL | PostgreSQL | 典型用法 |
|---|---|---|---|
| 短文本（名称、标题） | VARCHAR(64~255) | VARCHAR(64~255) | `name`、`title`、`nick_name` |
| 中等文本（描述） | VARCHAR(512) 或 TEXT | VARCHAR(512) 或 TEXT | `description`、`version_note` |
| 长文本（Markdown、日志） | MEDIUMTEXT 或 TEXT | TEXT | `description_md`、`content_md`、`log_text` |
| ID 值 | VARCHAR(128) | VARCHAR(128) | 所有 ID 和 `_id` 引用列 |
| MD5 | VARCHAR(64) | VARCHAR(64) | `file_md5` |
| 文件路径 | VARCHAR(512) | VARCHAR(512) | `object_name`、`file_path` |
| JSON | JSON / TEXT | JSON / TEXT | 见上文 JSON 列部分 |

---

## 数值类型

| 场景 | 类型 | 典型用法 |
|---|---|---|
| 标志位（0/1） | INT | `_flag` 列 |
| 计数 | INT | `_count` 列 |
| 排序序号 | INT | `sort_order` |
| 排名 | INT | `rank_no` |
| 版本号 | INT | `version_no` |
| 文件大小 | BIGINT | `file_size`（字节） |
| 分数 | DECIMAL 或 DOUBLE | `score`、`avg_score`、`best_score` |
