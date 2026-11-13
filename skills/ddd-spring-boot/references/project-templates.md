# Optional Project Implementation Templates

Use a section only when the user has selected its options or the target project already
uses them. These are adaptable examples, not instructions to install libraries or replace
existing contracts. See [project-conventions.md](project-conventions.md) for independent
choices and [project-config.md](project-config.md) for compatibility checks.

The main example assumes **explicit selection** of Spring Boot 3 / Jakarta Validation,
mutable Lombok DTOs, Command/View names, `R<T>`, the business-exception/code option, and
Spring transactions. These choices are not bundled requirements. For Boot 2 adapt Jakarta
imports to its actual `javax` dependencies. Java syntax is Java 8-compatible, but Boot 3
itself requires a newer runtime. No PageHelper or MyBatis dependency is needed for the main
example. Each public class/interface belongs in its own named file.

## Contents

- [Request and Response DTOs](#request-and-response-dtos)
- [Controller](#controller)
- [Application Service and Event Port](#application-service-and-event-port)
- [Application Service Test](#application-service-test)
- [Business Error Codes and Exceptions](#business-error-codes-and-exceptions)
- [Global Exception Handler](#global-exception-handler)
- [Optional PageHelper Pagination](#optional-pagehelper-pagination)
- [Optional Direct Persistence Mapping](#optional-direct-persistence-mapping)

## Request and Response DTOs

These DTOs go in `com.example.project.backend.application.dto.feature` for this example.
Lombok and validation choices can be replaced independently. Inline message text here does
not override an existing project requirement to use message constants or localization.

```java
package com.example.project.backend.application.dto.feature;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class CreateFeatureCommand {
    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "名称不能超过100个字符")
    private String name;
    private String description;
}
```

```java
package com.example.project.backend.application.dto.feature;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class UpdateFeatureCommand {
    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "名称不能超过100个字符")
    private String name;
    private String description;
}
```

The path ID is the single authority for update identity; this command has no duplicate body
ID to disagree with it. If an existing API requires a body ID, validate consistency explicitly.

```java
package com.example.project.backend.application.dto.feature;

import lombok.Data;

@Data
public class QueryFeatureCommand {
    private String name;
}
```

`QueryFeatureCommand` illustrates a separately selectable query DTO. Add it to an endpoint
only when a real query contract and implementation exist; the core example has no list/page
method that pretends to apply an unused filter.

```java
package com.example.project.backend.application.dto.feature;

import lombok.Data;

@Data
public class FeatureView {
    private String id;
    private String name;
    private String description;
    private boolean archived;
}
```

## Controller

This controller selects `R<T>` but not `BaseController`, pagination, or action-style deletion.
It does not imply selecting an `api` module. Keep existing route contracts in a real project.

```java
package com.example.project.backend.controller;

import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.FeatureView;
import com.example.project.backend.application.dto.feature.UpdateFeatureCommand;
import com.example.project.backend.application.service.FeatureApplicationService;
import com.example.project.common.domain.R;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/features")
@RequiredArgsConstructor
public class FeatureController {
    private final FeatureApplicationService featureService;

    @PostMapping
    public R<String> create(@Valid @RequestBody CreateFeatureCommand command) {
        return R.ok(featureService.create(command));
    }

    @PostMapping("/{id}")
    public R<Void> update(@PathVariable("id") String id,
                          @Valid @RequestBody UpdateFeatureCommand command) {
        featureService.update(id, command);
        return R.ok();
    }

    @GetMapping("/{id}")
    public R<FeatureView> getDetail(@PathVariable("id") String id) {
        return R.ok(featureService.getDetail(id));
    }
}
```

## Application Service and Event Port

Use `Feature`, `FeatureCreated`, and `FeatureRepository` from
[domain-templates.md](domain-templates.md). UUID IDs and this view mapping are example
implementation choices, not domain requirements.

The port below specifies a transactional contract, not a complete delivery implementation:
an adapter must register events inside the transaction and ensure that rollback does not
deliver a success event. Choose and implement a transaction-aware handler or outbox before
using it. Plain synchronous `ApplicationEventPublisher.publishEvent` is not sufficient to
claim this contract is met. Acceptance into an in-memory transaction callback does not
guarantee durable delivery; choose an outbox if needed.

```java
package com.example.project.backend.application.event;

import com.example.project.backend.domain.feature.FeatureCreated;
import java.util.List;

public interface FeatureEventRegistration {
    void registerForCommit(List<FeatureCreated> events);
}
```

```java
package com.example.project.backend.application.service;

import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.FeatureView;
import com.example.project.backend.application.dto.feature.UpdateFeatureCommand;
import com.example.project.backend.application.event.FeatureEventRegistration;
import com.example.project.backend.domain.feature.Feature;
import com.example.project.backend.domain.feature.FeatureRepository;
import com.example.project.backend.exception.NotFoundException;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class FeatureApplicationService {
    private final FeatureRepository featureRepository;
    private final FeatureEventRegistration eventRegistration;

    @Transactional
    public String create(CreateFeatureCommand command) {
        Feature feature = Feature.create(UUID.randomUUID().toString(),
                command.getName(), command.getDescription());
        featureRepository.save(feature);
        eventRegistration.registerForCommit(feature.pendingEvents());
        feature.clearPendingEvents();
        return feature.getId();
    }

    @Transactional
    public void update(String id, UpdateFeatureCommand command) {
        Feature feature = findOrThrow(id);
        feature.updateInfo(command.getName(), command.getDescription());
        featureRepository.save(feature);
    }

    @Transactional(readOnly = true)
    public FeatureView getDetail(String id) {
        Feature feature = findOrThrow(id);
        FeatureView view = new FeatureView();
        view.setId(feature.getId());
        view.setName(feature.getName());
        view.setDescription(feature.getDescription());
        view.setArchived(feature.isArchived());
        return view;
    }

    private Feature findOrThrow(String id) {
        return featureRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Feature not found: " + id));
    }
}
```

The standalone domain example uses standard Java exceptions to avoid a project dependency.
For a production feature, choose explicit business failures and their boundary mapping;
do not turn all Java argument/state exceptions into client errors. The handler below maps
only the selected business hierarchy and HTTP validation; an unmapped domain-example failure
will intentionally receive the generic internal-error fallback until adapted.

## Application Service Test

This section additionally assumes JUnit 5 and Mockito. It checks orchestration, not the
transactional adapter. Separate integration tests should verify commit, rollback, delivery,
and retries for the chosen event mechanism. Pure domain cases remain in domain examples.

```java
package com.example.project.backend.application.service;

import com.example.project.backend.application.dto.feature.CreateFeatureCommand;
import com.example.project.backend.application.dto.feature.UpdateFeatureCommand;
import com.example.project.backend.application.event.FeatureEventRegistration;
import com.example.project.backend.domain.feature.Feature;
import com.example.project.backend.domain.feature.FeatureRepository;
import com.example.project.backend.exception.NotFoundException;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class FeatureApplicationServiceTest {
    @Mock private FeatureRepository repository;
    @Mock private FeatureEventRegistration events;
    @InjectMocks private FeatureApplicationService service;

    @Test
    void createsAndRegistersEvents() {
        CreateFeatureCommand command = new CreateFeatureCommand();
        command.setName("Example");
        assertNotNull(service.create(command));
        verify(repository).save(any(Feature.class));
        verify(events).registerForCommit(argThat(pending -> pending.size() == 1
                && "Example".equals(pending.get(0).getName())));
    }

    @Test
    void usesPathIdentityForUpdate() {
        Feature feature = Feature.reconstruct("path-id", "Old", null, false);
        when(repository.findById("path-id")).thenReturn(Optional.of(feature));
        UpdateFeatureCommand command = new UpdateFeatureCommand();
        command.setName("New");
        service.update("path-id", command);
        assertEquals("New", feature.getName());
        verify(repository).save(feature);
    }

    @Test
    void reportsMissingFeature() {
        when(repository.findById("missing")).thenReturn(Optional.empty());
        assertThrows(NotFoundException.class, () -> service.getDetail("missing"));
    }
}
```

## Business Error Codes and Exceptions

Use these only if the user selects this hierarchy and scheme; otherwise retain the existing
error model. Values match the optional table in project conventions. Domain-specific classes
hold their own constants rather than extending this final class with a private constructor.

```java
package com.example.project.backend.exception;

public final class BizErrorCode {
    private BizErrorCode() {}
    public static final int SUCCESS = 200;
    public static final int BAD_REQUEST = 40000;
    public static final int INVALID_PARAMETER = 40001;
    public static final int FORBIDDEN = 40300;
    public static final int NO_ADMIN_ACCESS = 40301;
    public static final int NOT_FOUND = 40400;
    public static final int ALREADY_DELETED = 40401;
    public static final int ALREADY_EXISTS = 40900;
    public static final int NAME_CONFLICT = 40901;
    public static final int INTERNAL_ERROR = 50000;
    public static final int THIRD_PARTY_TIMEOUT = 50001;
}
```

```java
package com.example.project.backend.exception;

public final class WorkspaceErrorCode {
    private WorkspaceErrorCode() {}
    public static final int WORKSPACE_NOT_FOUND = 40410;
    public static final int WORKSPACE_NAME_DUPLICATE = 40910;
    public static final int WORKSPACE_LIMIT_EXCEEDED = 40010;
}
```

```java
package com.example.project.backend.exception;

public class BizException extends RuntimeException {
    private final int code;

    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }

    public BizException(String message) {
        this(BizErrorCode.INTERNAL_ERROR, message);
    }

    public BizException(int code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
    }

    public int getCode() { return code; }
}
```

Each subclass below belongs in its own file, in `com.example.project.backend.exception`.
Each offers a default and a specific code override. The permission subtype retains the
`OperationException` relationship.

```java
package com.example.project.backend.exception;

public class NotFoundException extends BizException {
    public NotFoundException(String message) { this(BizErrorCode.NOT_FOUND, message); }
    public NotFoundException(int code, String message) { super(code, message); }
}
```

```java
package com.example.project.backend.exception;

public class DeletedException extends BizException {
    public DeletedException(String message) { this(BizErrorCode.ALREADY_DELETED, message); }
    public DeletedException(int code, String message) { super(code, message); }
}
```

```java
package com.example.project.backend.exception;

public class AlreadyExistsException extends BizException {
    public AlreadyExistsException(String message) { this(BizErrorCode.ALREADY_EXISTS, message); }
    public AlreadyExistsException(int code, String message) { super(code, message); }
}
```

```java
package com.example.project.backend.exception;

public class OperationException extends BizException {
    public OperationException(String message) { this(BizErrorCode.BAD_REQUEST, message); }
    public OperationException(int code, String message) { super(code, message); }
}
```

```java
package com.example.project.backend.exception;

public class OperationPermissionException extends OperationException {
    public OperationPermissionException(String message) { this(BizErrorCode.FORBIDDEN, message); }
    public OperationPermissionException(int code, String message) { super(code, message); }
}
```

## Global Exception Handler

This example additionally assumes Lombok logging and the optional bundled/existing
`ServiceException`. It intentionally shows **envelope mapping only**; configure HTTP status
mapping separately to preserve the target API contract. Deliberate business/validation
messages must be safe to expose. Unexpected and platform failures receive a generic message.
Adapt additional MVC validation/parse exceptions for the actual Spring version and endpoints.

```java
package com.example.project.backend.exception;

import com.example.project.common.domain.R;
import com.example.project.common.exception.ServiceException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BizException.class)
    public R<Void> handleBusiness(BizException failure) {
        log.warn("Business failure: code={}", failure.getCode());
        return R.fail(failure.getCode(), failure.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public R<Void> handleValidation(MethodArgumentNotValidException failure) {
        FieldError error = failure.getBindingResult().getFieldError();
        String message = error == null ? "参数校验失败" : error.getDefaultMessage();
        return R.fail(BizErrorCode.INVALID_PARAMETER, message);
    }

    @ExceptionHandler(ServiceException.class)
    public R<Void> handlePlatform(ServiceException failure) {
        log.error("Platform failure", failure);
        return R.fail(BizErrorCode.INTERNAL_ERROR, "系统异常，请稍后重试");
    }

    @ExceptionHandler(Exception.class)
    public R<Void> handleUnexpected(Exception failure) {
        log.error("Unexpected failure", failure);
        return R.fail(BizErrorCode.INTERNAL_ERROR, "系统异常，请稍后重试");
    }
}
```

## Optional PageHelper Pagination

This is a **separate choice** from `R<T>`. Only after selecting PageHelper and its response
contract, adapt `BaseController` and use `startPage()` immediately before the intended query,
then `getDataTable(results)`. Implement a real filtered query service rather than adding an
unimplemented `paged()` call to the application example above.

Before reuse, address the bundled controller's Servlet namespace, bound page sizes, and
allowlist sorting fields/directions; see
[project-config.md](project-config.md#compatibility-and-adaptation-gates). Do not forward raw
request `orderBy` text to SQL. If those gates are not satisfied, do not copy the controller.

## Optional Direct Persistence Mapping

This alternative is only for a project/user that chooses to map domain objects directly with
MyBatis-Plus. It is **not** part of the framework-independent model above, and is not a second
class to copy alongside that `Feature` unchanged.

In this option, a project entity may use `@TableName(value = "feature", keepGlobalPrefix = true)`,
`@TableId`, a selected audit `BaseEntity`, and `@TableField(exist = false)` on pending events
or domain-only collections. An implementation may extend `ServiceImpl<Mapper, Entity>` and
its mapper may extend `BaseMapper<Entity>`; those types stay in infrastructure, not repository
contracts. Map value objects with an explicit converter/type handler as required.

Keep state transitions behind business methods. ORM reconstruction requirements do not justify
unrestricted public setters on an aggregate; if Lombok is selected, prefer targeted `@Getter`
over `@Data`/chain setters on domain roots. Ensure persistence can restore state without
creation events. Alternatively use separate persistence DOs with their own data-access
annotations and converters. Adopt neither strategy automatically and do not refactor existing
models merely to match these recommendations.
