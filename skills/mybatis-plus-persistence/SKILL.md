---
name: mybatis-plus-persistence
description: |
  MyBatis-Plus persistence layer conventions for DDD-style Spring Boot projects. Use this skill
  when writing or modifying MyBatis mapper interfaces, repository implementations, entity mapping
  annotations (@TableName, @TableId, @TableField, @TableLogic), custom TypeHandlers, or any
  database-related persistence code. Also use when creating new tables/entities, writing queries
  with MyBatis-Plus Wrappers (lambdaQuery, lambdaUpdate), or dealing with BaseEntity audit fields
  and logical delete. Even if the user just says "add a new table", "create a repository", or
  "write a database query", this skill applies as long as the project uses MyBatis-Plus.
---

# MyBatis-Plus Persistence Conventions

This skill covers the persistence layer in a DDD-style Spring Boot + MyBatis-Plus project. The
persistence layer lives in `infrastructure` and implements repository interfaces defined in the
`domain` layer (Dependency Inversion Principle).

MyBatis-Plus is the ORM, but entities are also domain objects — they carry both business logic
and persistence annotations. This dual role is intentional and keeps the model cohesive.

## Three Key Components

Every persisted aggregate has three pieces:

1. **Mapper** — MyBatis-Plus data access interface, extends `BaseMapper<T>`
2. **Repository Interface** — defined in the domain layer, returns domain types
3. **Repository Implementation** — in infrastructure, extends `ServiceImpl<Mapper, Entity>` and implements the domain interface

```
domain/
  Feature.java              ← entity with @TableName, @TableId, etc.
  FeatureRepository.java    ← interface: findById, save, delete...
infrastructure/
  persistence/mapper/
    FeatureMapper.java      ← @Mapper, extends BaseMapper<Feature>
  repository/
    FeatureRepositoryImpl.java ← @Repository, extends ServiceImpl<FeatureMapper, Feature>
                                    implements FeatureRepository
```

Read `references/mapper-repo-templates.md` for copy-paste templates of each component.

## Entity Mapping Annotations

Entities use MyBatis-Plus annotations to map to database tables. The entity class is also the
domain aggregate root — it carries both business behavior and persistence metadata.

### Core Annotations

| Annotation | Purpose | Example |
|------------|---------|---------|
| `@TableName` | Map class to table | `@TableName(value = "workspace", keepGlobalPrefix = true)` |
| `@TableId` | Primary key field | `@TableId` on the `id` field |
| `@TableField` | Column mapping, fill strategy, non-persisted fields | See below |
| `@TableLogic` | Logical delete flag | On `deletedFlag` field in `BaseEntity` |

### @TableField Usage

`@TableField` serves three distinct purposes in this codebase:

**1. Exclude fields from persistence** — domain-only collections and domain events:

```java
@TableField(exist = false)
private final Set<WorkspaceMember> members = new HashSet<>();

@TableField(exist = false)
private final List<DomainEvent> domainEvents = new ArrayList<>();
```

These fields hold in-memory domain data that is loaded separately and assembled by the repository.

**2. Auto-fill audit fields** — handled by MyBatis-Plus meta-object handler:

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

**3. Column name mapping** (when field name differs from column):

```java
@TableField("workspace_kind")
private String workspaceKind;
```

Read `references/entity-mapping.md` for the full entity mapping reference.

## BaseEntity and Audit Fields

All aggregate roots extend `BaseEntity`, which provides:

- `createTime` — set on insert
- `updateTime` — set on insert and update
- `createBy` — user ID who created the record
- `updateBy` — user ID who last updated the record
- `deletedFlag` — logical delete (`@TableLogic`): 0 = active, 1 = deleted

The `deletedFlag` means records are never physically removed. Queries automatically exclude
deleted records (MyBatis-Plus handles this via `@TableLogic`). When you need to check if an
entity is deleted in domain logic:

```java
public boolean isDeleted() {
    return this.getDeletedFlag().equals(1);
}
```

## Mapper Interface

Mappers are the thinnest possible layer — just the `@Mapper` interface extending `BaseMapper<T>`:

```java
@Mapper
public interface FeatureMapper extends BaseMapper<Feature> {
}
```

MyBatis-Plus provides all standard CRUD methods (`selectById`, `insert`, `updateById`, `deleteById`,
`selectList`, etc.) through `BaseMapper`. Only add custom methods when you need queries that can't
be expressed with MyBatis-Plus Wrappers.

Custom queries use `@Select` / `@Update` annotations on the mapper:

```java
@Mapper
public interface WorkspaceMapper extends BaseMapper<Workspace> {
    @Select("SELECT * FROM workspace WHERE name = #{name} AND deleted_flag = 0")
    Workspace selectByName(@Param("name") String name);
}
```

## Repository Implementation

Repository implementations bridge the domain and persistence layers:

```java
@Repository
@RequiredArgsConstructor
public class FeatureRepositoryImpl extends ServiceImpl<FeatureMapper, Feature>
        implements FeatureRepository {

    @Override
    public Optional<Feature> findById(String id) {
        return Optional.ofNullable(lambdaQuery()
                .eq(Feature::getId, id)
                .one());
    }

    @Override
    public void save(Feature feature) {
        saveOrUpdate(feature);
    }

    @Override
    public List<Feature> findAll() {
        return lambdaQuery().list();
    }
}
```

Key patterns:

- Extend `ServiceImpl<Mapper, Entity>` to get `saveOrUpdate`, `lambdaQuery`, `lambdaUpdate` for free.
- Use `lambdaQuery()` for type-safe queries — avoids string-based column names.
- Use `lambdaUpdate()` for type-safe updates.
- The `save()` method typically delegates to `saveOrUpdate()` which handles both insert and update.
- Return domain types (`Feature`, `Optional<Feature>`) from the domain interface, not DTOs.

For complex queries that need multi-table joins or dynamic SQL, write custom XML mappers or use
`@Select` annotations on the mapper interface.

## Query Patterns

### Simple query by field

```java
Optional<Feature> findByName(String name) {
    return Optional.ofNullable(lambdaQuery()
            .eq(Feature::getName, name)
            .one());
}
```

### List with conditions

```java
List<Feature> findByCategory(String category) {
    return lambdaQuery()
            .eq(Feature::getCategory, category)
            .orderByDesc(Feature::getCreateTime)
            .list();
}
```

### Paginated query

Pagination is handled at the controller level via `startPage()` (PageHelper). The repository
just returns the full list, and PageHelper intercepts the SQL to add pagination:

```java
// In repository — return all matching records
List<Feature> findAll() {
    return lambdaQuery()
            .orderByDesc(Feature::getCreateTime)
            .list();
}

// In controller — PageHelper adds LIMIT/OFFSET
startPage();
return getDataTable(featureService.paged());
```

### Update with conditions

```java
void updateStatus(String id, Integer status) {
    lambdaUpdate()
            .eq(Feature::getId, id)
            .set(Feature::getStatus, status)
            .update();
}
```

## Enum Persistence

Enums are persisted using MyBatis `EnumTypeHandler`. The default strategy stores the enum's
`name()` as a string. For custom ordinal or code-based mapping, configure a custom type handler.

Common enum pattern:

```java
public enum StatusEnum {
    ACTIVE, INACTIVE, ARCHIVED;
}
```

Mapped automatically to `"ACTIVE"`, `"INACTIVE"`, `"ARCHIVED"` in the database column.

## Custom TypeHandlers

The project uses custom TypeHandlers for special column types:

- **JsonTypeHandler** — maps JSON columns to/from Java objects (e.g., `Labels` value object stored as JSON)
- **MybatisPlusTimeHandler** — handles `LocalDateTime` conversion for the database driver

Place custom TypeHandlers in `infrastructure/config/` and register them globally or per-field:

```java
@TableField(typeHandler = JsonTypeHandler.class)
private Labels labels;
```

## No Foreign Key Constraints

The project explicitly does not model database foreign-key constraints. Relationships between
aggregates (e.g., workspace → members, workspace → datasets) are maintained through ID references
in code, not through FK constraints in the database. This means:

- Don't add FK-based assumptions or cascade delete logic.
- Relationships are loaded and assembled in memory by the repository.
- Referential integrity is enforced by the domain layer, not the database.

## Composite Loading Pattern

When an aggregate has non-persisted collections (members, resources), the repository loads them
separately and assembles the entity:

```java
@Override
public Optional<Workspace> findById(String id) {
    Workspace workspace = getById(id);
    if (workspace == null) {
        return Optional.empty();
    }

    // Load related entities and set them on the aggregate
    List<WorkspaceMember> members = workspaceMemberMapper.selectList(
            new LambdaQueryWrapper<WorkspaceMember>()
                    .eq(WorkspaceMember::getWorkspaceId, id));
    workspace.setMembers(members);

    // Set lazy loader for on-demand loading
    workspace.setMembers(() ->
            workspaceMemberMapper.selectList(
                    new LambdaQueryWrapper<WorkspaceMember>()
                            .eq(WorkspaceMember::getWorkspaceId, id)));

    return Optional.of(workspace);
}
```

This pattern uses `@TableField(exist = false)` fields on the entity and populates them through
separate queries in the repository.

## References

| File | When to read |
|------|-------------|
| `references/mapper-repo-templates.md` | Need copy-paste templates for Mapper, Repository, and TypeHandler |
| `references/entity-mapping.md` | Full reference for @TableName, @TableId, @TableField, BaseEntity fields, and annotation combinations |
