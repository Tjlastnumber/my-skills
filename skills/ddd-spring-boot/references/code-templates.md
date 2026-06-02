# Code Templates

Copy-paste templates for common tasks. Adjust names and packages to match the project.

## Table of Contents

1. [Controller](#controller)
2. [Application Service](#application-service)
3. [Create Command DTO](#create-command-dto)
4. [Update Command DTO](#update-command-dto)
5. [Query DTO](#query-dto)
6. [View DTO](#view-dto)
7. [Domain Entity (Aggregate Root)](#domain-entity-aggregate-root)
8. [Value Object](#value-object)
9. [Domain Event](#domain-event)
10. [Domain Service](#domain-service)
11. [Application Service Test](#application-service-test)
12. [Domain Entity Test](#domain-entity-test)

## Controller

```java
package com.example.project.backend.controller;

import com.example.project.common.domain.R;
import com.example.project.common.web.controller.BaseController;
import com.example.project.common.web.page.TableDataInfo;
import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.UpdateFeatureCommand;
import com.example.project.backend.application.dto.feature.QueryFeatureCommand;
import com.example.project.backend.application.dto.feature.FeatureView;
import com.example.project.backend.application.service.FeatureApplicationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/features")
public class FeatureController extends BaseController {

    private final FeatureApplicationService featureService;

    public FeatureController(FeatureApplicationService featureService) {
        this.featureService = featureService;
    }

    @PostMapping
    public R<String> create(@Valid @RequestBody CreateFeatureCommand command) {
        return R.ok(featureService.create(command));
    }

    @PostMapping("/{id}")
    public R<Void> update(@PathVariable String id,
                          @Valid @RequestBody UpdateFeatureCommand command) {
        featureService.update(command);
        return R.ok();
    }

    @GetMapping("/{id}")
    public R<FeatureView> getDetail(@PathVariable String id) {
        return R.ok(featureService.getDetail(id));
    }

    @GetMapping
    public R<List<FeatureView>> list(QueryFeatureCommand query) {
        return R.ok(featureService.list(query));
    }

    @GetMapping("/page")
    public TableDataInfo<?> paged(QueryFeatureCommand query) {
        startPage();
        return getDataTable(featureService.paged(query));
    }

    @PostMapping("/{id}/delete")
    public R<Void> delete(@PathVariable String id) {
        featureService.delete(id);
        return R.ok();
    }
}
```

## Application Service

```java
package com.example.project.backend.application.service;

import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.FeatureView;
import com.example.project.backend.application.dto.feature.UpdateFeatureCommand;
import com.example.project.backend.domain.event.DomainEventPublisher;
import com.example.project.backend.domain.feature.Feature;
import com.example.project.backend.domain.feature.FeatureRepository;
import com.example.project.backend.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
@RequiredArgsConstructor
public class FeatureApplicationService {

    private final FeatureRepository featureRepository;
    private final DomainEventPublisher eventPublisher;

    public String create(CreateFeatureCommand command) {
        Feature feature = Feature.create(command.getName(), command.getDescription());
        featureRepository.save(feature);
        publishEvents(feature);
        return feature.getId();
    }

    public void update(UpdateFeatureCommand command) {
        Feature feature = findOrThrow(command.getId());
        feature.updateInfo(command.getName(), command.getDescription());
        featureRepository.save(feature);
        publishEvents(feature);
    }

    public void delete(String id) {
        Feature feature = findOrThrow(id);
        featureRepository.deleteById(id);
    }

    @Transactional(readOnly = true)
    public FeatureView getDetail(String id) {
        Feature feature = findOrThrow(id);
        return convertToView(feature);
    }

    @Transactional(readOnly = true)
    public List<FeatureView> list() {
        return featureRepository.findAll().stream()
                .map(this::convertToView)
                .collect(Collectors.toList());
    }

    private Feature findOrThrow(String id) {
        return featureRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Feature not found: " + id));
    }

    private void publishEvents(Feature feature) {
        feature.getDomainEvents().forEach(eventPublisher::publish);
        feature.clearDomainEvents();
    }

    private FeatureView convertToView(Feature feature) {
        FeatureView view = new FeatureView();
        view.setId(feature.getId());
        view.setName(feature.getName());
        view.setDescription(feature.getDescription());
        view.setCreateTime(feature.getCreateTime());
        return view;
    }
}
```

## Create Command DTO

```java
package com.example.project.backend.application.dto.feature;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class CreateFeatureCommand {

    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "名称不能超过100个字符")
    private String name;

    private String description;
}
```

## Update Command DTO

```java
package com.example.project.backend.application.dto.feature;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotBlank;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class UpdateFeatureCommand {

    @NotBlank(message = "ID不能为空")
    private String id;

    @NotBlank(message = "名称不能为空")
    private String name;

    private String description;
}
```

## Query DTO

```java
package com.example.project.backend.application.dto.feature;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class QueryFeatureCommand {

    private String name;
    private String keyword;
}
```

## View DTO

```java
package com.example.project.backend.application.dto.feature;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
public class FeatureView {

    private String id;
    private String name;
    private String description;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
```

## Domain Entity (Aggregate Root)

```java
package com.example.project.backend.domain.feature;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.example.project.backend.domain.AggregateRoot;
import com.example.project.backend.domain.BaseEntity;
import com.example.project.backend.domain.event.DomainEvent;
import com.example.project.backend.exception.OperationException;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

@Data
@TableName(value = "feature", keepGlobalPrefix = true)
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = true)
public class Feature extends BaseEntity implements AggregateRoot {

    @TableId
    private String id;

    private String name;

    private String description;

    @TableField(exist = false)
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    public static Feature create(String name, String description) {
        if (name == null || name.trim().isEmpty()) {
            throw new OperationException("名称不能为空");
        }
        Feature feature = new Feature();
        feature.id = java.util.UUID.randomUUID().toString();
        feature.name = name;
        feature.description = description;
        return feature;
    }

    public static Feature reconstruct(String id, String name, String description,
                                      String createBy, String updateBy) {
        Feature feature = new Feature();
        feature.id = id;
        feature.name = name;
        feature.description = description;
        feature.setCreateBy(createBy);
        feature.setUpdateBy(updateBy);
        return feature;
    }

    public void updateInfo(String newName, String newDescription) {
        if (newName == null || newName.trim().isEmpty()) {
            throw new OperationException("名称不能为空");
        }
        this.name = newName;
        this.description = newDescription;
        this.setUpdateTime(LocalDateTime.now());
    }

    private void addDomainEvent(DomainEvent event) {
        this.domainEvents.add(event);
    }

    public List<DomainEvent> getDomainEvents() {
        return Collections.unmodifiableList(domainEvents);
    }

    public void clearDomainEvents() {
        domainEvents.clear();
    }
}
```

## Value Object

```java
package com.example.project.backend.domain.feature.valueobject;

import com.example.project.backend.exception.OperationException;

public class FeatureName {

    private static final int MAX_LENGTH = 100;

    private final String value;

    private FeatureName(String value) {
        this.value = value;
    }

    public static FeatureName of(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new OperationException("名称不能为空");
        }
        if (value.length() > MAX_LENGTH) {
            throw new OperationException("名称不能超过" + MAX_LENGTH + "个字符");
        }
        return new FeatureName(value);
    }

    public String getValue() {
        return value;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof FeatureName)) return false;
        return value.equals(((FeatureName) o).value);
    }

    @Override
    public int hashCode() {
        return value.hashCode();
    }
}
```

## Domain Event

```java
package com.example.project.backend.domain.feature;

import com.example.project.backend.domain.event.DomainEvent;

public class FeatureCreatedEvent extends DomainEvent {

    private final String featureId;
    private final String featureName;

    public FeatureCreatedEvent(String featureId, String featureName) {
        super();
        this.featureId = featureId;
        this.featureName = featureName;
    }

    public String getFeatureId() {
        return featureId;
    }

    public String getFeatureName() {
        return featureName;
    }
}
```

## Domain Service

```java
package com.example.project.backend.domain.feature;

import com.example.project.backend.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class FeatureDomainService {

    private final FeatureRepository featureRepository;

    public Feature getOrThrow(String featureId) {
        return featureRepository.findById(featureId)
                .orElseThrow(() -> new NotFoundException("Feature not found: " + featureId));
    }

    public void validateNameUnique(String name) {
        featureRepository.findByName(name).ifPresent(existing -> {
            throw new OperationException("名称已存在: " + name);
        });
    }
}
```

## Application Service Test

```java
package com.example.project.backend.application.service;

import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.FeatureView;
import com.example.project.backend.domain.event.DomainEventPublisher;
import com.example.project.backend.domain.feature.Feature;
import com.example.project.backend.domain.feature.FeatureRepository;
import com.example.project.backend.exception.NotFoundException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class FeatureApplicationServiceTest {

    @Mock
    private FeatureRepository featureRepository;

    @Mock
    private DomainEventPublisher eventPublisher;

    @InjectMocks
    private FeatureApplicationService service;

    @Nested
    @DisplayName("create feature")
    class CreateFeature {

        @Test
        @DisplayName("should create and return ID")
        void shouldCreate() {
            CreateFeatureCommand command = new CreateFeatureCommand();
            command.setName("test-feature");
            command.setDescription("desc");

            String id = service.create(command);

            assertNotNull(id);
            verify(featureRepository).save(any(Feature.class));
        }

        @Test
        @DisplayName("should throw when name is blank")
        void shouldThrowOnBlankName() {
            CreateFeatureCommand command = new CreateFeatureCommand();
            command.setName("");

            assertThrows(OperationException.class, () -> service.create(command));
        }
    }

    @Nested
    @DisplayName("get detail")
    class GetDetail {

        @Test
        @DisplayName("should return view when found")
        void shouldReturnView() {
            Feature feature = Feature.reconstruct("id-1", "name", "desc", "user", null);
            when(featureRepository.findById("id-1")).thenReturn(Optional.of(feature));

            FeatureView view = service.getDetail("id-1");

            assertEquals("id-1", view.getId());
            assertEquals("name", view.getName());
        }

        @Test
        @DisplayName("should throw when not found")
        void shouldThrowNotFound() {
            when(featureRepository.findById("missing")).thenReturn(Optional.empty());

            assertThrows(NotFoundException.class, () -> service.getDetail("missing"));
        }
    }
}
```

## Domain Entity Test

```java
package com.example.project.backend.domain.feature;

import com.example.project.backend.exception.OperationException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class FeatureTest {

    @Nested
    @DisplayName("create")
    class Create {

        @Test
        @DisplayName("should create with valid input")
        void shouldCreate() {
            Feature feature = Feature.create("my-feature", "description");

            assertNotNull(feature.getId());
            assertEquals("my-feature", feature.getName());
            assertEquals("description", feature.getDescription());
        }

        @Test
        @DisplayName("should throw when name is null")
        void shouldThrowOnNullName() {
            assertThrows(OperationException.class, () -> Feature.create(null, "desc"));
        }

        @Test
        @DisplayName("should throw when name is empty")
        void shouldThrowOnEmptyName() {
            assertThrows(OperationException.class, () -> Feature.create("", "desc"));
        }
    }

    @Nested
    @DisplayName("updateInfo")
    class UpdateInfo {

        @Test
        @DisplayName("should update name and description")
        void shouldUpdate() {
            Feature feature = Feature.create("old-name", "old-desc");
            feature.updateInfo("new-name", "new-desc");

            assertEquals("new-name", feature.getName());
            assertEquals("new-desc", feature.getDescription());
            assertNotNull(feature.getUpdateTime());
        }

        @Test
        @DisplayName("should throw when new name is blank")
        void shouldThrowOnBlankName() {
            Feature feature = Feature.create("name", "desc");
            assertThrows(OperationException.class, () -> feature.updateInfo("", "desc"));
        }
    }
}
```
