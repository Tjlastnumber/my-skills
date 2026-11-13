# Optional Project Convention Recommendations

These are a menu of implementation choices, **not mandatory rules or requirements of DDD**.
Prefer the target project's existing conventions. Where a needed choice is absent, explain
the relevant options and let the user choose all, some, an alternative, or none before applying
them. Loading this skill or reading these recommendations is not consent to adopt them.

## Contents

- [Selection and Compatibility](#selection-and-compatibility)
- [Java and Dependency Injection](#java-and-dependency-injection)
- [DTOs and Validation](#dtos-and-validation)
- [HTTP Responses and Pagination](#http-responses-and-pagination)
- [Exceptions and Business Codes](#exceptions-and-business-codes)
- [Code Style and Imports](#code-style-and-imports)
- [Testing and Builds](#testing-and-builds)

## Selection and Compatibility

Treat each row as independent unless its dependency is stated. Record relevant existing
conventions and explicit user choices in the task response; no new configuration file is needed.

| Choice | Recommendation if the user wants one | Alternatives / prerequisites |
| --- | --- | --- |
| Dependency injection | Constructor injection; optionally Lombok `@RequiredArgsConstructor` | Explicit constructors; Lombok only if selected/already used |
| DTO names | `*Command`, `*Query`, `*View` | Existing Request/Response/DTO names are equally usable |
| Input validation | Bean Validation at the HTTP boundary | Match the project's `javax` or `jakarta` namespace and validation setup |
| API responses | `R<T>` if a business envelope is desired | Plain DTOs, `ResponseEntity`, existing envelopes |
| Pagination | `TableDataInfo<T>` and optionally PageHelper | Spring Data, MyBatis-Plus pagination, existing query strategy |
| Exceptions | Typed business exceptions and centralized adapter handling | Existing exception/result model |
| Business codes | Centralized constants and the illustrative ranges below | Existing codes; no envelope codes when HTTP semantics suffice |
| Layout | Optional `api/core/backend` separation | Single module or other existing boundaries |
| Style | Four-space indentation, explicit imports | Existing formatter/style configuration |
| Tests | JUnit 5; Mockito for isolated collaborators | Existing framework, fakes, integration tests where needed |
| Build entry point | Existing wrapper, if present | Detected Maven/Gradle commands; no invented script paths |

Selecting a response envelope does not select PageHelper, exception codes, or a module layout.
Selecting DDD does not select any row. Do not introduce libraries or change public protocols
merely to match the examples. Use [project-config.md](project-config.md) to adapt only the
selected options, and [project-templates.md](project-templates.md) for implementation examples.

## Java and Dependency Injection

Read the actual build configuration before generating code. Version compatibility is a
technical constraint, not a choice that this skill can override. Do not upgrade Java or Spring
as a side effect of selecting another recommendation.

| Feature | Minimum Java version |
| --- | --- |
| `List.of()`, `Set.of()`, `Map.of()` | 9 |
| `Stream.takeWhile()`, `dropWhile()`, `ofNullable()` | 9 |
| Local variable `var` | 10 (Lombok `val` is a separate library feature) |
| Switch expressions | 14 |
| Text blocks | 15 |
| Records, pattern matching for `instanceof` | 16 |
| Sealed classes | 17 |
| Pattern matching for switch, virtual threads | 21 |

For new beans, constructor injection makes dependencies explicit and supports plain unit tests.
If the user chooses Lombok, `@RequiredArgsConstructor` with `private final` dependencies is a
concise implementation; otherwise an explicit constructor provides the same design. An
existing explicit constructor need not be rewritten. Optional dependencies can use
`ObjectProvider<T>` if that fits the selected Spring approach.

Use DTO mutability annotations only as needed by binding/serialization. Do not expose domain
setters simply to reuse a DTO pattern. Match local `Optional`, collection, and stream usage
instead of opportunistically modernizing unrelated code.

## DTOs and Validation

If the user selects these names, group DTOs by feature under the existing application/interface
boundary. A possible location is `application.dto.workspace`; it is not a required package.

| Role | Suggested pattern | Example |
| --- | --- | --- |
| Create request | `Create*Command` or `*CreateCommand` / `*SaveCommand` | `CreateWorkspaceCommand` |
| Update request | `Update*Command` or `*UpdateCommand` | `UpdateWorkspaceCommand` |
| Other operation | `*Command` | `AssociateResourceCommand` |
| Query/filter | `*Query` or `Query*Command` | `QueryWorkspaceCommand` |
| Response | `*View` | `WorkspaceView` |

Lombok `@Data` on mutable request/response DTOs and `@Accessors(chain = true)` on views are
separate optional choices. Immutable DTOs are also valid if the target framework supports them.

If Bean Validation is selected/already in use, common annotations include `@NotBlank`,
`@NotEmpty`, `@Size`, `@NotNull`, and `@Pattern`. Use `@Valid` for nested/request-body validation
and configure method validation according to the actual Spring version (often `@Validated`).
Spring Boot 2 normally uses `javax.validation`; Spring Boot 3 uses `jakarta.validation`.

Avoid duplicating transport-only checks unnecessarily, but **keep business invariants in the
domain** even when an HTTP DTO checks similar values. Jobs and event handlers can bypass HTTP.
Match existing message language/constant conventions; this skill does not mandate either
inline messages or a constants class.

## HTTP Responses and Pagination

If selected, controllers can wrap single-resource results with `R.ok(data)` and errors with
`R.fail(code, message)`. A response envelope's business code is distinct from HTTP status.
Preserve the target project's chosen HTTP semantics rather than assuming all responses are 200.

The optional PageHelper pattern is `startPage()` followed immediately by the intended query
and `getDataTable(...)`, returning `TableDataInfo<T>`. It requires suitable query execution
and a compatible dependency. If the application returns a projection or already uses another
pagination mechanism, retain it rather than forcing this controller base.

Use an existing common library where it provides the selected contract. Bundled classes in
`scripts/common-infrastructure/` are candidate implementations only; do not copy them by default.
See the Servlet compatibility and sorting safety notes in [project-config.md](project-config.md).

Other independent choices illustrated in older project code include String IDs,
`LocalDateTime` timestamps, and action routes such as `POST /{id}/delete`. Preserve existing
route/ID/time contracts; these examples are not recommendations to replace UUID, numeric IDs,
`Instant`, or REST-style deletion. If an `api` module already defines contracts, update affected
implementations and consumers together without requiring that module in other projects.

## Exceptions and Business Codes

If selected, this hierarchy offers typed failures and centralized translation:

```text
RuntimeException
├── BizException
│   ├── NotFoundException
│   ├── DeletedException
│   ├── AlreadyExistsException
│   └── OperationException
│       └── OperationPermissionException
└── ServiceException
```

Keep business failure meaning independent of HTTP. The optional `BizException` below carries
an application business code, not an HTTP response; domain examples do not require it.
Reuse existing error strategies instead of adding a second hierarchy.

If the user also selects envelope business codes, a possible scheme is:

| Range | Category | Example mapping |
| --- | --- | --- |
| `200` | Success | `R.ok(...)` |
| `40000–40099` | Invalid input / operation | `OperationException`: `40000`; validation: `40001` |
| `40300–40399` | Permission | `OperationPermissionException`: `40300` |
| `40400–40499` | Missing / deleted resource | `NotFoundException`: `40400`; `DeletedException`: `40401` |
| `40900–40999` | Conflict / duplicate | `AlreadyExistsException`: `40900` |
| `50000–50099` | System / platform failure | fallback: `50000`; third-party timeout: `50001` |

For this selected scheme, centralize values in a class or enum such as `BizErrorCode`.
Exceptions carry a code, and a `@RestControllerAdvice` can translate it to the selected
response contract. Give validation and uncoded platform failures explicit defaults. Optional
domain sub-ranges (e.g. `40410–40419`) can avoid collisions; use independent constants classes
rather than subclassing a final utility class. Do not adopt these ranges over existing codes.

Throw errors at the point a business rule fails; do not silently return null or swallow invalid
states. Application services arrange operations and may report a missing aggregate, while
business decisions remain in the domain. Catch locally when adapting an external failure;
translate at the boundary without leaking sensitive internal messages to clients.

## Code Style and Imports

If the user needs a new style and selects this one, a reasonable starting point is four spaces,
same-line opening braces, one annotation per line, a blank line between methods, and explicit
imports. Suggested import groups are project, third-party, `javax.*`/`jakarta.*`, then `java.*`.
Static imports are useful in tests. Short Chinese or English comments can explain business
concepts where names alone are insufficient.

Existing formatter rules and local conventions take precedence. Preserve nearby spacing,
wildcards, and syntax when a task does not request a style change. No unrelated reformatting
is needed to use this skill.

## Testing and Builds

If selected, JUnit 5 with Mockito supports focused application tests using
`@ExtendWith(MockitoExtension.class)`, `@Mock`, `@InjectMocks`, `when`/`verify`, and `assertThrows`.
`@Nested`, `@DisplayName`, and `assertAll` can organize cases. Pure domain tests usually need
neither mocks nor a Spring context. Use integration tests for transaction/event behavior,
persistence mappings, or MVC behavior that a mock-based test cannot verify.

Follow the actual build entry point. Prefer the existing wrapper when available (`./mvnw`,
`./gradlew`, or a repository script); do not require `./scripts/mvn-wrapper.sh` or invent an
environment-check script. Confirm module names, profiles, and test filters before running
commands from [project-config.md](project-config.md). Adding a wrapper or switching build
tools is a separate user choice, not a prerequisite of DDD.
