# Mapper and Repository Templates

## Table of Contents

1. [Mapper Interface (Basic)](#mapper-interface-basic)
2. [Mapper Interface (With Custom Queries)](#mapper-interface-with-custom-queries)
3. [Repository Interface (Domain Layer)](#repository-interface-domain-layer)
4. [Repository Implementation (Basic)](#repository-implementation-basic)
5. [Repository Implementation (Composite Loading)](#repository-implementation-composite-loading)
6. [Repository Implementation (With Update)](#repository-implementation-with-update)
7. [Custom TypeHandler (JSON)](#custom-typehandler-json)
8. [Custom TypeHandler (Enum)](#custom-typehandler-enum)
9. [XML Mapper (Complex Queries)](#xml-mapper-complex-queries)

## Mapper Interface (Basic)

```java
package com.example.project.backend.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.project.backend.domain.feature.Feature;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FeatureMapper extends BaseMapper<Feature> {
}
```

This is sufficient for all standard CRUD. MyBatis-Plus provides:
- `selectById(id)`, `selectBatchIds(ids)`
- `selectList(wrapper)`, `selectOne(wrapper)`
- `insert(entity)`, `updateById(entity)`
- `deleteById(id)`, `deleteBatchIds(ids)`
- `selectCount(wrapper)`

## Mapper Interface (With Custom Queries)

```java
package com.example.project.backend.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.project.backend.domain.workspace.Workspace;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface WorkspaceMapper extends BaseMapper<Workspace> {

    @Select("SELECT * FROM workspace WHERE name = #{name} AND deleted_flag = 0 LIMIT 1")
    Workspace selectByName(@Param("name") String name);

    @Select("SELECT COUNT(*) FROM workspace WHERE create_by = #{userId} AND deleted_flag = 0")
    int countByCreator(@Param("userId") String userId);
}
```

Only add custom SQL when the query cannot be expressed with `lambdaQuery()` / `LambdaQueryWrapper`.

## Repository Interface (Domain Layer)

Defined in the domain layer — returns domain types only, never DTOs:

```java
package com.example.project.backend.domain.feature;

import java.util.List;
import java.util.Optional;

public interface FeatureRepository {

    Optional<Feature> findById(String id);

    List<Feature> findAll();

    List<Feature> findByName(String name);

    void save(Feature feature);

    void deleteById(String id);
}
```

## Repository Implementation (Basic)

```java
package com.example.project.backend.infrastructure.repository;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.project.backend.domain.feature.Feature;
import com.example.project.backend.domain.feature.FeatureRepository;
import com.example.project.backend.infrastructure.persistence.mapper.FeatureMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class FeatureRepositoryImpl extends ServiceImpl<FeatureMapper, Feature>
        implements FeatureRepository {

    @Override
    public Optional<Feature> findById(String id) {
        return Optional.ofNullable(getById(id));
    }

    @Override
    public List<Feature> findAll() {
        return lambdaQuery()
                .orderByDesc(Feature::getCreateTime)
                .list();
    }

    @Override
    public List<Feature> findByName(String name) {
        return lambdaQuery()
                .like(Feature::getName, name)
                .list();
    }

    @Override
    public void save(Feature feature) {
        saveOrUpdate(feature);
    }

    @Override
    public void deleteById(String id) {
        removeById(id);
    }
}
```

Note: `removeById` performs a logical delete (sets `deleted_flag = 1`) because `BaseEntity`
uses `@TableLogic`. The record is not physically deleted.

## Repository Implementation (Composite Loading)

When an aggregate has related entities stored in separate tables, load and assemble them in the
repository:

```java
package com.example.project.backend.infrastructure.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.project.backend.domain.workspace.Workspace;
import com.example.project.backend.domain.workspace.WorkspaceMember;
import com.example.project.backend.domain.workspace.WorkspaceRepository;
import com.example.project.backend.infrastructure.persistence.mapper.WorkspaceMapper;
import com.example.project.backend.infrastructure.persistence.mapper.WorkspaceMemberMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;

@Repository
@RequiredArgsConstructor
public class WorkspaceRepositoryImpl extends ServiceImpl<WorkspaceMapper, Workspace>
        implements WorkspaceRepository {

    private final WorkspaceMemberMapper workspaceMemberMapper;

    @Override
    public Optional<Workspace> findById(String id) {
        Workspace workspace = getById(id);
        if (workspace == null) {
            return Optional.empty();
        }

        // Eagerly load members
        List<WorkspaceMember> members = workspaceMemberMapper.selectList(
                new LambdaQueryWrapper<WorkspaceMember>()
                        .eq(WorkspaceMember::getWorkspaceId, id));
        workspace.setMembers(members);

        // Set lazy loader for on-demand refresh
        Supplier<List<WorkspaceMember>> memberLoader = () ->
                workspaceMemberMapper.selectList(
                        new LambdaQueryWrapper<WorkspaceMember>()
                                .eq(WorkspaceMember::getWorkspaceId, id));
        workspace.setMembers(memberLoader);

        return Optional.of(workspace);
    }

    @Override
    public void save(Workspace workspace) {
        saveOrUpdate(workspace);

        // Persist members separately
        for (WorkspaceMember member : workspace.getMembers()) {
            workspaceMemberMapper.insert(member);
        }
    }

    @Override
    public void deleteById(String id) {
        removeById(id);

        // Also logically delete members
        workspaceMemberMapper.delete(
                new LambdaQueryWrapper<WorkspaceMember>()
                        .eq(WorkspaceMember::getWorkspaceId, id));
    }
}
```

The entity uses `@TableField(exist = false)` for these collections — they are not mapped to
columns in the aggregate's table.

## Repository Implementation (With Update)

```java
@Override
public void updateMemberRole(String workspaceId, String userId, RoleEnum role) {
    lambdaUpdate()
            .eq(WorkspaceMember::getWorkspaceId, workspaceId)
            .eq(WorkspaceMember::getUserId, userId)
            .set(WorkspaceMember::getRole, role)
            .update();
}

@Override
public int countByWorkspaceId(String workspaceId) {
    return (int) lambdaQuery(WorkspaceMember.class)
            .eq(WorkspaceMember::getWorkspaceId, workspaceId)
            .count();
}
```

## Custom TypeHandler (JSON)

For storing complex objects as JSON in a VARCHAR/TEXT column:

```java
package com.example.project.backend.infrastructure.config;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedJdbcTypes;
import org.apache.ibatis.type.MappedTypes;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

@MappedTypes(Object.class)
@MappedJdbcTypes(JdbcType.VARCHAR)
public class JsonTypeHandler extends BaseTypeHandler<Object> {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i,
                                     Object parameter, JdbcType jdbcType) throws SQLException {
        try {
            ps.setString(i, MAPPER.writeValueAsString(parameter));
        } catch (JsonProcessingException e) {
            throw new SQLException("Error converting object to JSON", e);
        }
    }

    @Override
    public Object getNullableResult(ResultSet rs, String columnName) throws SQLException {
        return parseJson(rs.getString(columnName));
    }

    @Override
    public Object getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        return parseJson(rs.getString(columnIndex));
    }

    @Override
    public Object getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        return parseJson(cs.getString(columnIndex));
    }

    private Object parseJson(String json) {
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return MAPPER.readValue(json, Object.class);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error parsing JSON", e);
        }
    }
}
```

Usage on entity field:

```java
@TableField(typeHandler = JsonTypeHandler.class)
private Labels labels;
```

## Custom TypeHandler (Enum)

For enums that store an integer code instead of the name:

```java
package com.example.project.backend.infrastructure.config;

import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class EnumCodeTypeHandler<E extends Enum<E>> extends BaseTypeHandler<E> {

    private final Class<E> type;
    private final E[] enums;

    public EnumCodeTypeHandler(Class<E> type) {
        this.type = type;
        this.enums = type.getEnumConstants();
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i,
                                     E parameter, JdbcType jdbcType) throws SQLException {
        ps.setInt(i, parameter.ordinal());
    }

    @Override
    public E getNullableResult(ResultSet rs, String columnName) throws SQLException {
        int code = rs.getInt(columnName);
        return rs.wasNull() ? null : toEnum(code);
    }

    @Override
    public E getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        int code = rs.getInt(columnIndex);
        return rs.wasNull() ? null : toEnum(code);
    }

    @Override
    public E getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        int code = cs.getInt(columnIndex);
        return cs.wasNull() ? null : toEnum(code);
    }

    private E toEnum(int code) {
        if (code < 0 || code >= enums.length) {
            throw new IllegalArgumentException("Unknown enum code: " + code);
        }
        return enums[code];
    }
}
```

## XML Mapper (Complex Queries)

For multi-table joins or dynamic SQL that can't be expressed with annotations, use XML mappers:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.project.backend.infrastructure.persistence.mapper.WorkspaceMapper">

    <resultMap id="workspaceDetailMap" type="com.example.project.backend.domain.workspace.Workspace">
        <id property="id" column="id"/>
        <result property="name" column="name"/>
        <result property="description" column="description"/>
        <result property="createTime" column="create_time"/>
        <result property="updateTime" column="update_time"/>
    </resultMap>

    <select id="selectWorkspaceDetail" resultMap="workspaceDetailMap">
        SELECT w.*, COUNT(m.id) as member_count
        FROM workspace w
        LEFT JOIN workspace_member m ON w.id = m.workspace_id AND m.deleted_flag = 0
        WHERE w.id = #{id} AND w.deleted_flag = 0
        GROUP BY w.id
    </select>

</mapper>
```

XML mapper files go in `backend/src/main/resources/mapper/` and are registered in
`application.yml`:

```yaml
mybatis-plus:
  mapper-locations: classpath*:mapper/**/*.xml
```
