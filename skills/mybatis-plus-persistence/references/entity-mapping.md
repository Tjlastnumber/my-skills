# Entity Mapping Reference

Detailed reference for MyBatis-Plus entity annotations and how they combine with DDD domain
modeling.

## Table of Contents

1. [Annotation Summary](#annotation-summary)
2. [@TableName](#tablename)
3. [@TableId](#tableid)
4. [@TableField](#tablefield)
5. [@TableLogic](#tablelogic)
6. [BaseEntity Audit Fields](#baseentity-audit-fields)
7. [Entity Annotation Combinations](#entity-annotation-combinations)
8. [Non-Persisted Domain Fields](#non-persisted-domain-fields)
9. [Value Object Persistence](#value-object-persistence)

## Annotation Summary

| Annotation | Where | Purpose |
|------------|-------|---------|
| `@TableName` | Class | Maps entity class to a database table |
| `@TableId` | Field | Marks the primary key field |
| `@TableField` | Field | Column mapping, fill strategy, type handler, exclude from persistence |
| `@TableLogic` | Field | Logical delete flag — SELECT queries auto-add `WHERE deleted_flag = 0` |

## @TableName

Maps the entity class to a database table.

```java
@TableName(value = "workspace", keepGlobalPrefix = true)
public class Workspace extends BaseEntity implements AggregateRoot {
```

Parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `value` | Class name (lowercase) | Table name |
| `keepGlobalPrefix` | `false` | Whether to keep the global table prefix configured in MyBatis-Plus |
| `autoResultMap` | `false` | Auto-build result map (needed when using custom TypeHandlers) |

When using `autoResultMap = true` (required for `@TableField(typeHandler = ...)` on result fields):

```java
@TableName(value = "workspace", keepGlobalPrefix = true, autoResultMap = true)
public class Workspace extends BaseEntity implements AggregateRoot {
```

## @TableId

Marks the primary key field. By default, MyBatis-Plus uses a snowflake ID strategy.

```java
@TableId
private String id;
```

Common strategies:

| Strategy | Description |
|----------|-------------|
| `IdType.ASSIGN_ID` (default) | Snowflake-based long ID |
| `IdType.ASSIGN_UUID` | UUID string |
| `IdType.INPUT` | User provides the ID (no auto-generation) |

In this project, IDs are `String` type and typically generated in the domain entity's `create()`
factory method using `UUID.randomUUID().toString()`:

```java
public static Workspace create(String name, String createdBy) {
    Workspace ws = new Workspace();
    ws.id = UUID.randomUUID().toString(); // Domain-generated ID
    // ...
    return ws;
}
```

This means the entity uses `IdType.INPUT` or relies on the application to set the ID before insert.

## @TableField

The most versatile annotation — used for column mapping, auto-fill, type handlers, and excluding
fields from persistence.

### Column name mapping

When the Java field name doesn't match the database column (after MyBatis-Plus camelCase →
snake_case conversion):

```java
@TableField("workspace_kind")
private String workspaceKind;
```

### Auto-fill strategy

Audit fields in `BaseEntity` use fill strategies. A `MetaObjectHandler` implementation intercepts
inserts and updates to set these values automatically.

| Strategy | When filled |
|----------|------------|
| `FieldFill.INSERT` | Only on insert (e.g., `createTime`, `createBy`) |
| `FieldFill.INSERT_UPDATE` | On insert and every update (e.g., `updateTime`) |
| `FieldFill.UPDATE` | Only on update (e.g., `updateBy`) |
| `FieldFill.DEFAULT` | No auto-fill |

```java
@TableField(fill = FieldFill.INSERT)
private LocalDateTime createTime;

@TableField(fill = FieldFill.INSERT_UPDATE)
private LocalDateTime updateTime;

@TableField(fill = FieldFill.INSERT)
private String createBy;

@TableField(fill = FieldFill.UPDATE)
private String updateBy;
```

### Custom TypeHandler

For fields that need special conversion (JSON, custom enum codes):

```java
@TableField(typeHandler = JsonTypeHandler.class)
private Labels labels;
```

**Important**: When using `typeHandler` on a field that needs to be populated by SELECT queries,
you must set `autoResultMap = true` on `@TableName`:

```java
@TableName(value = "workspace", autoResultMap = true)
public class Workspace extends BaseEntity {
    @TableField(typeHandler = JsonTypeHandler.class)
    private Labels labels;
}
```

### Exclude from persistence

Domain-only fields that don't correspond to any database column:

```java
@TableField(exist = false)
private final Set<WorkspaceMember> members = new HashSet<>();

@TableField(exist = false)
private final Set<String> environmentIds = new HashSet<>();

@TableField(exist = false)
private final List<DomainEvent> domainEvents = new ArrayList<>();

@TableField(exist = false)
private Supplier<List<WorkspaceMember>> memberMethod;
```

These fields are populated by the repository implementation through separate queries or setters.
The `exist = false` parameter tells MyBatis-Plus to skip them during INSERT/UPDATE/SELECT.

## @TableLogic

Marks the logical delete flag. MyBatis-Plus automatically adds `WHERE deleted_flag = 0` to all
SELECT queries and changes `DELETE` to `UPDATE SET deleted_flag = 1`.

```java
@TableLogic
private Integer deletedFlag;
```

This is defined in `BaseEntity`, so all entities inherit it. The convention:

| Value | Meaning |
|-------|---------|
| `0` | Active (not deleted) |
| `1` | Deleted |

When you call `removeById(id)` or `lambdaUpdate().remove()`, MyBatis-Plus executes:

```sql
UPDATE workspace SET deleted_flag = 1 WHERE id = ?
```

When you call `getById(id)` or `lambdaQuery().list()`, it automatically adds:

```sql
WHERE deleted_flag = 0
```

## BaseEntity Audit Fields

All entities extend `BaseEntity` which provides five common fields:

```java
@Data
public class BaseEntity {
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;

    @TableField(fill = FieldFill.UPDATE)
    private String updateBy;

    @TableLogic
    private Integer deletedFlag;
}
```

The `MetaObjectHandler` (usually in `infrastructure/config/`) sets these values:

```java
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "createBy", String.class, getCurrentUserId());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
        this.strictUpdateFill(metaObject, "updateBy", String.class, getCurrentUserId());
    }
}
```

## Entity Annotation Combinations

A typical aggregate root entity combines Lombok + MyBatis-Plus + DDD annotations:

```java
@Data                                                    // Lombok: getters, setters, toString
@TableName(value = "workspace", keepGlobalPrefix = true) // MyBatis-Plus: table mapping
@Accessors(chain = true)                                 // Lombok: setter returns this
@EqualsAndHashCode(callSuper = true)                     // Lombok: include BaseEntity fields
public class Workspace extends BaseEntity implements AggregateRoot {

    @TableId
    private String id;

    private String name;

    private String description;

    @TableField(exist = false)
    private final Set<WorkspaceMember> members = new HashSet<>();

    @TableField(exist = false)
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    // Static factory methods, business methods, domain event management...
}
```

Annotation order convention:
1. Lombok class-level: `@Data`, `@Accessors`, `@EqualsAndHashCode`
2. MyBatis-Plus class-level: `@TableName`
3. Spring class-level: `@Service`, `@Repository` (not on entities)
4. Field-level: `@TableId`, then `@TableField`, then other annotations

## Non-Persisted Domain Fields

These `@TableField(exist = false)` fields fall into categories:

**1. Domain collections** — related entities loaded by the repository:

```java
@TableField(exist = false)
private final Set<WorkspaceMember> members = new HashSet<>();
```

**2. ID references** — IDs of related aggregates, used for validation before persisting:

```java
@TableField(exist = false)
private final Set<String> environmentIds = new HashSet<>();
```

**3. Domain events** — collected by the entity, published by the application service:

```java
@TableField(exist = false)
private final List<DomainEvent> domainEvents = new ArrayList<>();
```

**4. Lazy loaders** — supplier functions for on-demand loading:

```java
@TableField(exist = false)
private Supplier<List<WorkspaceMember>> memberMethod;
```

All use `final` with initialization to `new HashSet<>()` / `new ArrayList<>()` so they're never
null. Access through getters that may trigger lazy loading.

## Value Object Persistence

Value objects (like `WorkspaceName`, `WorkspaceId`) are typically not stored as separate columns
with custom types. Instead, the entity stores the raw value and converts:

```java
// Entity stores the raw string
private String name;

// Conversion happens in domain methods
public void updateInfo(String newName) {
    this.name = WorkspaceName.of(newName).getValue(); // validate, then store
}

public WorkspaceName getWorkspaceName() {
    return WorkspaceName.of(this.name); // reconstitute value object on read
}
```

For value objects that need special persistence (e.g., a `Labels` map stored as JSON), use a
custom TypeHandler:

```java
@TableField(typeHandler = JsonTypeHandler.class)
private Labels labels;
```

The `Labels` class must be serializable to/from JSON by Jackson.
