---
name: ddd-spring-boot
description: |
  DDD-style Spring Boot development conventions for Java projects with a layered architecture
  (controller → application.service → domain → infrastructure). Use this skill when working on
  any Spring Boot project that follows DDD patterns: writing controllers, application services,
  domain entities, value objects, DTOs, exception handling, or unit tests. Also use when setting
  up Maven build commands, configuring Java compatibility, or making code-style decisions in a
  DDD-flavored Spring Boot codebase. Even if the user just says "add a new feature" or "fix this
  service" without mentioning DDD, this skill applies as long as the project uses this architecture.
---

# DDD Spring Boot Development Conventions

This skill captures proven conventions from a production DDD-style Spring Boot + MyBatis-Plus project.
The goal is to keep code consistent, maintainable, and aligned with the layered architecture — not
to add ceremony for its own sake.

When in doubt about a convention, read `references/project-config.md` for this project's specific
settings, and `references/architecture.md` for a deeper explanation of the layering.

## Java Version Compatibility

This skill does not lock a specific Java version. The project's Java version is determined by
its `pom.xml` (`maven.compiler.source` / `maven.compiler.target` / `<java.version>`) or the
equivalent Gradle setting. Before writing new code, confirm the project's Java version and use
syntax that is compatible with it.

Version-sensitive syntax (use only if the project's Java version is >= the listed minimum):

| Feature | Minimum Java version |
|---------|---------------------|
| `var` (local variable type inference) | 10 (or 8 with `+`-style Lombok `val`, project-dependent) |
| `List.of()`, `Set.of()`, `Map.of()` | 9 |
| `Stream.takeWhile()` / `dropWhile()` / `ofNullable()` | 9 |
| Text blocks (`"""..."""`) | 15 |
| Records (`record`) | 16 (finalized) |
| Switch expressions | 14 (finalized) |
| Pattern matching for `instanceof` | 16 |
| Sealed classes | 17 |
| Pattern matching for switch | 21 |
| Virtual threads (`Thread.ofVirtual()`) | 21 |

Rules:

- Read the project's `pom.xml` to determine the Java version before writing code. Do not assume a specific version.
- Write code that is compatible with the project's Java version. If in doubt, prefer the more conservative syntax.
- Keep style consistent within a single file. Don't introduce newer syntax into a file that is otherwise written in an older style.
- Do not opportunistically upgrade existing files to a newer Java syntax unless the task explicitly asks for it.
- `Optional` is fine where the codebase already uses it (domain repositories, lookup methods); don't introduce it gratuitously.
- Use `java.util` collections and streams in the same style as nearby code.

## Architecture and Layers

The backend follows a DDD-inspired layering. Each layer has a clear responsibility, and dependencies
flow inward — outer layers depend on inner layers, never the reverse.

```
controller          → handles HTTP, delegates to application services
application.service → orchestrates use cases, manages transactions, publishes events
domain              → entities, value objects, domain services, domain events
infrastructure      → repository implementations, persistence mappers, third-party adapters
```

For the full package layout and what belongs in each layer, read `references/architecture.md`.

Key rules:

- Business invariants live in domain entities and value objects. Don't let services bypass them.
- Domain entities use static factory methods (`create(...)`, `reconstruct(...)`) instead of raw constructors for meaningful creation.
- Application services orchestrate but contain no business rules themselves.
- Controllers are thin — they validate input (via `@Valid`), call the application service, and return `R<T>`.
- Keep shared API contracts in the `api` module (if the project has one), not in `backend`.

When adding a new feature that spans layers, create/update all related layers together:
controller ↔ application.dto ↔ application.service ↔ domain ↔ infrastructure.repository.

## Spring Dependency Injection

Constructor injection is the standard. The pattern keeps dependencies explicit and testable.

```java
@Service
@RequiredArgsConstructor
public class ExampleApplicationService {
    private final WorkspaceRepository workspaceRepository;
    private final DomainEventPublisher eventPublisher;
}
```

- Use Lombok `@RequiredArgsConstructor` for new beans — don't hand-write boilerplate constructors.
- All injected fields are `private final`.
- Do not add `@Autowired` or `@Resource` field injection.
- Optional dependencies can use `ObjectProvider<T>`.
- If an existing class already uses an explicit constructor without Lombok, keep that style unless you're already restructuring the class.

## DTO Naming Conventions

The naming pattern makes the role of each DTO immediately clear:

| Type | Naming | Example |
|------|--------|---------|
| Create request | `*CreateCommand` or `*SaveCommand` | `CreateWorkspaceCommand` |
| Update request | `*UpdateCommand` | `UpdateWorkspaceCommand` |
| General command | `*Command` | `AssociateResourceCommand` |
| Query/filter | `*Query` or `Query*Command` | `QueryWorkspaceCommand` |
| Response | `*View` | `WorkspaceView` |

Request DTOs typically use `@Data` (Lombok). View DTOs often add `@Accessors(chain = true)`.

Place DTOs under the `application.dto` package, grouped by domain in sub-packages:
```
application/dto/
├── workspace/
│   ├── CreateWorkspaceCommand.java
│   ├── UpdateWorkspaceCommand.java
│   ├── QueryWorkspaceCommand.java
│   └── WorkspaceView.java
└── notification/
    └── ...
```

## Validation

Validate request DTOs at the controller boundary using `javax.validation` annotations:

```java
@Data
public class CreateWorkspaceCommand {
    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "名称不能超过100个字符")
    private String name;

    private String description;
}
```

- Use `@Valid` on `@RequestBody` parameters in controllers.
- Use `@Validated` on the controller class if method-level validation is needed.
- Common annotations: `@NotBlank`, `@NotEmpty`, `@Size`, `@NotNull`, `@Pattern`.
- Don't duplicate validation logic in the service layer if it's already handled by annotations.

## Controller Conventions

Controllers are thin HTTP adapters. Their job is to receive input, validate, call the application
service, and wrap the result.

```java
@RestController
@RequestMapping("/workspaces")
public class WorkspaceController extends BaseController {

    private final WorkspaceApplicationService workspaceService;

    public WorkspaceController(WorkspaceApplicationService workspaceService) {
        this.workspaceService = workspaceService;
    }

    @PostMapping
    public R<String> create(@Valid @RequestBody CreateWorkspaceCommand command) {
        return R.ok(workspaceService.create(command));
    }

    @GetMapping("/{id}")
    public R<WorkspaceView> getDetail(@PathVariable String id) {
        return R.ok(workspaceService.getDetail(id));
    }

    @GetMapping("/page")
    public TableDataInfo<?> paged() {
        startPage();
        return getDataTable(workspaceService.paged());
    }

    @PostMapping("/{id}/delete")
    public R<Void> delete(@PathVariable String id) {
        workspaceService.delete(id);
        return R.ok();
    }
}
```

Key points:

- Single-resource responses return `R<T>`. Use `R.ok(data)` or `R.ok(data, message)`.
- Paginated queries use `startPage()` then `getDataTable(...)` from `BaseController`, returning `TableDataInfo<?>`.
- `R`, `BaseController`, `TableDataInfo`, and `ServiceException` are common infrastructure classes. If the project already has a common library providing them, use it. If not, ready-to-use implementations are in `scripts/common-infrastructure/` — copy them into the project's common package.
- Route style is mixed REST and action-like (e.g., `POST /{id}/delete`). Follow the existing controller's style — don't rename endpoints opportunistically.
- IDs are `String`. Timestamps are `LocalDateTime`.

If the project has an `api` module with interface contracts (e.g., `KubernetesApi`), controllers in `core` implement those interfaces. Update both sides together when changing the contract.

## Error Handling

The project has a structured exception hierarchy. Use it — don't return null to signal errors or
silently swallow invalid states.

The hierarchy (adapt names to your project):

```
RuntimeException
├── BizException          — base business exception
│   ├── NotFoundException — resource not found
│   ├── DeletedException  — resource already deleted
│   └── OperationException — general operation failure
│       └── OperationPermissionException — permission denied
└── ServiceException      — platform-level error
```

A `GlobalExceptionHandler` (`@RestControllerAdvice`) translates these into `R.fail(code, message)`:

| Exception | HTTP code in R |
|-----------|---------------|
| `NotFoundException` | 404 |
| `OperationException` | 400 |
| `OperationPermissionException` | 403 |
| `BizException` / `ServiceException` | 500 |
| Validation errors | 400 |

When to throw:

- Domain entity detects invalid state → throw the appropriate `BizException` subclass.
- Application service encounters a business rule violation → throw `OperationException` or a more specific subclass.
- Catch exceptions locally only when adapting third-party behavior (e.g., Kubernetes client failures). Let the `GlobalExceptionHandler` handle the rest.

Error messages can be in Chinese or English — match the style of the surrounding code.

## Domain Model

The domain layer uses the "rich model" approach: entities contain business logic, not just data.

### Aggregate Roots and Entities

```java
@Data
@TableName(value = "workspace", keepGlobalPrefix = true)
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = true)
public class Workspace extends BaseEntity implements AggregateRoot {

    @TableId
    private String id;

    private String name;

    // Non-persisted domain collections
    @TableField(exist = false)
    private final Set<WorkspaceMember> members = new HashSet<>();

    @TableField(exist = false)
    private final List<DomainEvent> domainEvents = new ArrayList<>();

    // Factory methods — the only way to create new instances with invariants
    public static Workspace create(String name, String description, String createdBy) {
        WorkspaceName workspaceName = WorkspaceName.of(name); // value object validates
        Workspace ws = new Workspace();
        ws.id = WorkspaceId.generate().getValue();
        ws.name = workspaceName.getValue();
        ws.description = description;
        ws.setCreateBy(createdBy);
        ws.addDomainEvent(new WorkspaceCreatedEvent(ws, createdBy));
        return ws;
    }

    public static Workspace reconstruct(String id, String name, ...) {
        // Rebuild from persistence — no validation, no events
        Workspace ws = new Workspace();
        ws.id = id;
        ws.name = name;
        // ...
        return ws;
    }

    // Business methods — invariants are enforced here
    public void addMember(String userId, RoleEnum role, String operationBy) {
        validatePermission(operationBy);
        validateMemberNotExist(userId);
        // ... add member, publish event
    }

    public void updateInfo(String newName, String updatedBy) {
        this.name = WorkspaceName.of(newName).getValue(); // value object validates
        this.setUpdateBy(updatedBy);
    }

    // Domain events
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

### Value Objects

Value objects enforce single-field invariants at construction time:

```java
public class WorkspaceName {
    private static final int MAX_LENGTH = 100;
    private final String value;

    private WorkspaceName(String value) {
        this.value = value;
    }

    public static WorkspaceName of(String value) {
        if (value == null || value.trim().isEmpty()) {
            throw new OperationException("工作区名称不能为空");
        }
        if (value.length() > MAX_LENGTH) {
            throw new OperationException("工作区名称不能超过" + MAX_LENGTH + "个字符");
        }
        return new WorkspaceName(value);
    }

    public String getValue() {
        return value;
    }
}
```

### Domain Events

Domain events represent things that happened in the domain. Aggregate roots collect them, and
application services publish them after the transaction commits.

```java
public abstract class DomainEvent {
    private final String eventId;
    private final LocalDateTime occurredOn;

    protected DomainEvent() {
        this.eventId = UUID.randomUUID().toString();
        this.occurredOn = LocalDateTime.now();
    }
}
```

### Domain Services

Use a domain service when a piece of logic doesn't naturally belong to a single entity or
needs to coordinate multiple aggregates:

```java
@Service
@RequiredArgsConstructor
public class TeamDomainService {
    private final TeamRepository teamRepository;

    public Team getTeamOrThrow(String teamId) {
        return teamRepository.findById(teamId)
                .orElseThrow(() -> new NotFoundException("团队未找到: " + teamId));
    }
}
```

## Code Style

These rules keep the codebase visually consistent. When touching a file, follow its existing style
rather than reformatting.

- **Indentation**: 4 spaces, no tabs.
- **Braces**: opening brace on the same line (`if (...) {`).
- **Annotations**: one per line, especially in Spring/Lombok classes.
- **Blank lines**: preserve existing spacing. One blank line between methods.
- **Comments**: sparse. The code should speak through names. Short Chinese comments are acceptable where the domain concept needs clarification.
- **Don't reformat** files you're only touching for a logic change.

## Import Order

Keep imports organized in stable groups:

1. Project imports (your project's base package)
2. Third-party imports (`com.baomidou...`, `lombok...`, `org.springframework...`)
3. `javax.*`
4. `java.*`

Prefer explicit imports. If a file already uses wildcard imports, keep the local style to avoid churn. Static imports are common and fine in test files.

## Testing

Test framework: JUnit 5 + Mockito.

```java
@ExtendWith(MockitoExtension.class)
class WorkspaceApplicationServiceTest {

    @Mock
    private WorkspaceRepository workspaceRepository;

    @Mock
    private DomainEventPublisher eventPublisher;

    @InjectMocks
    private WorkspaceApplicationService service;

    @Nested
    @DisplayName("create workspace")
    class CreateWorkspace {

        @Test
        @DisplayName("should create successfully with valid input")
        void shouldCreate() {
            // given
            CreateWorkspaceCommand command = new CreateWorkspaceCommand();
            command.setName("test-workspace");

            // when
            String id = service.create(command);

            // then
            assertNotNull(id);
            verify(workspaceRepository).save(any(Workspace.class));
        }

        @Test
        @DisplayName("should throw when name is blank")
        void shouldThrowOnBlankName() {
            CreateWorkspaceCommand command = new CreateWorkspaceCommand();
            command.setName("");

            assertThrows(OperationException.class, () -> service.create(command));
        }
    }
}
```

Testing patterns:

- `@ExtendWith(MockitoExtension.class)` — no Spring context in unit tests.
- `@Nested` to group related test cases within a class.
- `@DisplayName` with descriptive names (Chinese or English — match the project style).
- `@Mock` for dependencies, `@InjectMocks` for the system under test.
- `when(...).thenReturn(...)` / `verify(...)` for interaction testing.
- `assertThrows(...)` for expected exceptions.
- `assertAll(...)` to group multiple assertions.
- Prefer focused unit tests. Mock external dependencies. Don't load the full Spring context unless testing integration.

## Build Commands

This project uses Maven with wrapper scripts. The pattern generalizes to any project with a
build wrapper — always use the wrapper rather than invoking `mvn` directly.

Read `references/project-config.md` for the actual script paths and module names used in this project.

Typical commands:

| Action | Command pattern |
|--------|----------------|
| Validate env | `./scripts/ensure-build-env.sh` |
| Run all tests | `./scripts/mvn-wrapper.sh test` |
| Build all | `./scripts/mvn-wrapper.sh clean package -DskipTests` |
| Test one module | `./scripts/mvn-wrapper.sh -pl backend -am test` |
| Test one class | `./scripts/mvn-wrapper.sh -pl backend -am -Dtest=SomeTest test` |
| Test one method | `./scripts/mvn-wrapper.sh -pl backend -am -Dtest='SomeTest#method' test` |
| Run locally | `./scripts/mvn-wrapper.sh -pl backend -am spring-boot:run -Dspring-boot.run.profiles=local` |

## Agent Working Rules

These meta-rules govern how to approach any change:

- **Smallest correct change.** Don't refactor beyond what the task requires.
- **Follow existing patterns.** Don't replace local project style with generic "best practices" when the repo has a clear pattern.
- **Keep layers in sync.** When changing backend logic, check whether domain, repository, DTO, and controller layers need coordinated updates.
- **API contracts.** When changing `core` proxy endpoints, inspect the `api` module contracts too.
- **Always use the Maven wrapper.** Run Maven through the repo wrapper script from the repository root.

## References

For deeper details, read these files in the `references/` directory:

| File | When to read |
|------|-------------|
| `architecture.md` | Need the full package layout, layer responsibilities, or inter-module dependencies |
| `code-templates.md` | Want copy-paste templates for controllers, services, entities, tests |
| `project-config.md` | Need project-specific names: packages, exception classes, BaseEntity fields, Maven module names |

Common infrastructure implementations (copy into projects that lack a common library):

| File | What it provides |
|------|-----------------|
| `scripts/common-infrastructure/R.java` | `R<T>` unified response wrapper (`R.ok()`, `R.fail()`) |
| `scripts/common-infrastructure/TableDataInfo.java` | `TableDataInfo<T>` paginated response wrapper |
| `scripts/common-infrastructure/BaseController.java` | `BaseController` with `startPage()` / `getDataTable()` (requires PageHelper) |
| `scripts/common-infrastructure/ServiceException.java` | `ServiceException` platform-level exception |
