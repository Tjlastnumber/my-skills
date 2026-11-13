# Optional Project Configuration Examples

This document helps adapt **selected** recommendations to a target project. None of the
module names, packages, dependencies, classes, fields, or script paths below is mandatory.
Inspect the actual project first; use its existing configuration. Where a relevant choice is
missing, ask the user before adopting an example. See [project-conventions.md](project-conventions.md).

## Contents

- [Environment](#environment)
- [Optional Module Layout](#optional-module-layout)
- [Optional Package Layout](#optional-package-layout)
- [Optional Common Infrastructure](#optional-common-infrastructure)
- [Optional Exception Configuration](#optional-exception-configuration)
- [Optional Persistence and Domain Base Types](#optional-persistence-and-domain-base-types)
- [Build Entry Points and Commands](#build-entry-points-and-commands)

## Environment

| Item | How to determine the actual setting |
| --- | --- |
| Java | Effective Maven `release` / `maven.compiler.release`, source/target, parent properties such as `java.version`, or Gradle toolchain/compatibility |
| Spring Boot | Build plugins, parent, dependency management and resolved dependencies |
| Maven/Gradle | Existing wrapper configuration, build files, project instructions |
| Parent POM / group ID | Existing `pom.xml` and inherited configuration |
| `.sdkmanrc` | Optional project-managed environment pins; do not create unless requested |

Do not infer versions from these examples. Match resolved Spring/Servlet/Validation namespaces
and the chosen Java language level before adapting code.

## Optional Module Layout

One possible multi-module layout, useful when a project actually needs separate contracts,
a gateway, and a business service:

```text
<project-root>/
├── api/       # Shared contracts/models; no service implementation
├── core/      # Gateway/proxy service (optional)
├── backend/   # Business service
└── pom.xml
```

For this option, `core` implements `api` interfaces and `backend` can consume `api` models.
Neither service needs to depend on the other service's implementation. If an API contract
changes, inspect its implementations and consumers. Do not invent these modules for a project
that has no such deployment or contract boundary.

An optional gateway `core` may have `config`, `controller`, `filter`, `model`, `service`,
`support`, and `template` packages. Reactive types such as `Mono` and `ServerWebExchange`
belong there only when its selected framework needs them. A gateway need not have the same
domain layering as the business service. Kubernetes-facing examples are scenario-specific,
not an assumed dependency.

## Optional Package Layout

Example packages for the selected module layout:

| Module | Illustrative base package |
| --- | --- |
| `api` | `com.example.project.api` |
| `core` | `com.example.project.core` |
| `backend` | `com.example.project.backend` |

Within a business service, one possible arrangement is:

```text
backend/
├── config/
├── constant/
├── controller/
├── application/
│   ├── dto/workspace/       # CreateWorkspaceCommand, WorkspaceView, etc.
│   ├── eventhandler/
│   └── service/
├── domain/
│   ├── workspace/          # Aggregate, repository contract, value objects
│   ├── notification/
│   └── event/              # Event/dispatch contracts if shared
├── exception/
├── infrastructure/
│   ├── persistence/mapper/
│   └── repository/
└── utils/
```

Package-by-feature and other existing layouts can express the same boundaries. The names,
shared constants, utility package, and event locations are not DDD requirements. For design
responsibilities rather than package choices, see [architecture.md](architecture.md).

## Optional Common Infrastructure

Only when the user selects these contracts and the project lacks equivalents, consider the
bundled implementations. Do not add a common library simply because this table mentions it.

| Class | Illustrative target package | Bundled source |
| --- | --- | --- |
| `R<T>` | `com.example.project.common.domain` | `scripts/common-infrastructure/R.java` |
| `TableDataInfo<T>` | `com.example.project.common.web.page` | `scripts/common-infrastructure/TableDataInfo.java` |
| `BaseController` | `com.example.project.common.web.controller` | `scripts/common-infrastructure/BaseController.java` |
| `ServiceException` | `com.example.project.common.exception` | `scripts/common-infrastructure/ServiceException.java` |

The source paths are relative to the skill root. Existing libraries (e.g. a project's common
module) may already provide equivalent classes; reuse them after checking signatures.

### Compatibility and adaptation gates

- The bundled code uses Java 8-compatible syntax, but syntax compatibility does not imply
  compatibility with every Spring Boot version.
- `BaseController.java` imports `javax.servlet.http.HttpServletRequest`. Spring Boot 3 uses
  `jakarta.servlet`; adapt and test it if the user selects this option. It is not a drop-in
  Boot 3 implementation.
- The controller base depends on PageHelper; choose a compatible dependency only if the user
  selects PageHelper. Do not add it when the project already uses another pagination strategy.
- The bundled `BaseController` accepts request `orderBy` text directly. **Do not use that path
  with untrusted input unchanged.** If adopting it, map allowed sort fields/directions to
  trusted SQL identifiers before calling PageHelper. Validate/bound `pageNum` and `pageSize` too.
- `R` has default success/failure codes `200`/`500`. If the optional five-digit business-code
  scheme is selected, use explicit `R.fail(code, message)`; do not assume `R.fail(message)`
  emits `50000`. Coordinate contracts with clients before changing defaults.
- Review packages, serialization, HTTP semantics, exception-message exposure, and pagination
  behavior before copying. The original bundled files are unchanged by this documentation split.

## Optional Exception Configuration

If selected, place `BizErrorCode`, `BizException`, `NotFoundException`, `DeletedException`,
`AlreadyExistsException`, `OperationException`, `OperationPermissionException`, and
`GlobalExceptionHandler` in the project's chosen application/common boundary. Package
`com.example.project.backend.exception` is an example, not a required location.

The full optional hierarchy/code ranges live in
[project-conventions.md](project-conventions.md#exceptions-and-business-codes), and compatible
example implementations live in [project-templates.md](project-templates.md). Keep those as
the source for defaults instead of maintaining another mapping table here. Reuse existing
codes when present. Domain-specific code classes can hold independent constants, avoiding
inheritance from final utility classes.

## Optional Persistence and Domain Base Types

The following audit/logical-delete fields are one possible MyBatis-Plus mapping, **not required
domain fields**:

| Field | Example type | Example persistence strategy |
| --- | --- | --- |
| `createTime` | `LocalDateTime` | `FieldFill.INSERT` |
| `updateTime` | `LocalDateTime` | `FieldFill.INSERT_UPDATE` |
| `createBy` | `String` | `FieldFill.INSERT` |
| `updateBy` | `String` | `FieldFill.UPDATE` |
| `deletedFlag` | `Integer` | `@TableLogic`, 0 active / 1 deleted |

If the user chooses direct domain/persistence mapping, an audit `BaseEntity` and MyBatis-Plus
annotations can express this implementation trade-off. Alternatively keep audit fields on a
separate persistence model and map to domain factories. Do not change the project's chosen
strategy as part of this skill without a request.

An `AggregateRoot` marker interface is optional. `DomainEvent` metadata (`eventId`, occurrence
time) and a `DomainEventPublisher` port may be useful, but neither an inheritance hierarchy
nor a Spring publisher wrapper is required. If Spring events are selected, explicitly verify
transaction-aware handling; plain `publishEvent` alone is not an after-commit guarantee.

## Build Entry Points and Commands

Inspect scripts before using them. The historical example uses
`./scripts/ensure-build-env.sh` and `./scripts/mvn-wrapper.sh`; these are **not bundled by this
skill** and may not exist in the target project. Use `./mvnw`, `./gradlew`, an existing script,
or the project's documented direct command as applicable. Do not create or require a wrapper
without user selection.

For a project that actually uses Maven, replace `<maven-entry>` below with its detected entry
point and replace module/profile/test names. The placeholders are not literal shell commands.

| Action | Example command pattern |
| --- | --- |
| All tests | `<maven-entry> test` |
| Package without running tests | `<maven-entry> clean package -DskipTests` |
| Install | `<maven-entry> clean install` |
| Test module and required dependencies | `<maven-entry> -pl backend -am test` |
| Build contract module | `<maven-entry> -pl api -am package -DskipTests` |
| Test one class | `<maven-entry> -pl backend -am -Dtest=SomeTest test` |
| Test one method | `<maven-entry> -pl backend -am -Dtest='SomeTest#method' test` |
| Run a service | `<maven-entry> -pl backend spring-boot:run -Dspring-boot.run.profiles=local` |

With `-am`, test filters also affect upstream modules; adapt the test strategy when those
modules have no matching tests. Run the Spring Boot goal only on the runnable service module;
build/install its dependencies first if necessary, rather than trying to start every module.
An environment-check command is useful only if the project actually provides one.
