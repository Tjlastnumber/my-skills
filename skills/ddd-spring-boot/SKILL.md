---
name: ddd-spring-boot
description: |
  DDD modeling and layered design guidance for Spring Boot projects. Use when designing or
  changing aggregates, entities, value objects, domain services, repository boundaries,
  application services, or domain events, including feature work and refactoring in an
  existing DDD-style codebase. Also use when the user wants to review or choose Spring Boot
  project conventions, such as DTO naming, API responses, exceptions, tests, or build setup.
  Project conventions are optional recommendations, not requirements of DDD; applying this
  skill does not authorize introducing them.
---

# DDD Spring Boot

Separate **DDD design guidance** from **optional project conventions**. DDD describes how
to model business behavior and separate responsibilities; it does not prescribe an API
wrapper, ORM, pagination library, package name, Java version, or build script.

项目约定文档提供可选的推荐方案，不构成强制规范。遵循目标项目已有约定；新增或替换约定须由用户选择，不得因使用本 skill 而自动应用。

## Workflow

1. **Inspect the target project.** Read its instructions, nearby code, build configuration,
   and relevant tests. Identify the business use case, current boundaries, Java/Spring
   versions, and any conventions already in use. Do not assume this skill's examples
   describe the target project.
2. **Load only the relevant guidance.** Use the reading table below. For DDD-only tasks,
   do not load project templates or infrastructure files merely because they exist.
3. **Establish project choices when needed.** Follow existing project conventions. If a
   relevant choice has not been made, present the applicable recommendations and ask the
   user which, if any, to adopt. Users may select individual options, all options, or none.
   Reading a document, loading this skill, or asking for a feature is not consent to adopt
   its recommendations. Do not block unrelated work on choices it does not need.
4. **Design and implement the smallest coherent change.** Put business invariants in the
   domain, orchestration in the application layer, and technical adaptations at the edge.
   Check affected contracts, DTOs, repositories, and adapters without automatically
   creating every layer or forcing a new module/package structure.
5. **Verify and report.** Use the target project's actual verification commands. Check
   business behavior, layer dependencies, and relevant integration boundaries. Report
   existing conventions followed, new options explicitly selected, and unverified areas.

## Reading Guide

Paths are relative to this skill directory. Labels distinguish design guidance from choices.

| Category | Document | Read when |
| --- | --- | --- |
| DDD | [architecture.md](references/architecture.md) | Assigning responsibilities, reviewing dependencies, or defining repository boundaries |
| DDD | [domain-modeling.md](references/domain-modeling.md) | Designing aggregates, entities, value objects, domain services, or events |
| DDD examples | [domain-templates.md](references/domain-templates.md) | Needing framework-independent modeling and domain test examples |
| Optional recommendations | [project-conventions.md](references/project-conventions.md) | Reviewing or selecting DTO, DI, validation, API, exception, style, or testing options |
| Optional configuration examples | [project-config.md](references/project-config.md) | Adapting selected module layouts, packages, audit fields, dependencies, or build commands |
| Optional implementation examples | [project-templates.md](references/project-templates.md) | Implementing options already selected by the user or established in the target project |

## Boundaries and Failure Rules

- Do not present `R<T>`, `BaseController`, PageHelper, MyBatis-Plus, Lombok, an exception
  hierarchy, a business code range, or `api/core/backend` modules as requirements of DDD.
- Do not add dependencies, copy infrastructure classes, replace existing conventions, or
  impose naming/build/style choices without the user's selection. Preserve existing
  project contracts unless changing them is part of the request.
- Keep framework and persistence choices out of generic domain examples. An existing
  project may deliberately map domain objects directly to persistence; describe that as
  a project trade-off, not a universal DDD rule or an automatic refactoring request.
- If versions, transaction/event semantics, or conventions are unclear and affect the
  change, ask rather than guessing. Distinguish input validation from domain invariants;
  request annotations do not replace domain protection.
- If a recommended option conflicts with target-project instructions, surface the conflict
  instead of silently overriding those instructions.

## Optional Bundled Infrastructure

These files remain at their existing paths for compatibility. Use them only when the user
selects the corresponding option, the project lacks an equivalent, and compatibility has
been checked. They are examples to adapt, not automatically installed components.

| File | Option | Preconditions |
| --- | --- | --- |
| `scripts/common-infrastructure/R.java` | Unified response wrapper | User chooses this response contract |
| `scripts/common-infrastructure/TableDataInfo.java` | Paginated response | User chooses this pagination contract |
| `scripts/common-infrastructure/BaseController.java` | PageHelper controller base | PageHelper and Servlet compatibility; see project configuration notes |
| `scripts/common-infrastructure/ServiceException.java` | Platform exception | Fits the selected exception strategy |

## Verification Checklist

- Business rules cannot be bypassed through ordinary state mutation.
- Application orchestration and domain rules remain distinct; repository implementations
  and HTTP/persistence types do not leak into domain contracts unintentionally.
- Creation, state transitions, reconstruction, and event rollback behavior are tested as relevant.
- Every newly applied project recommendation has an explicit user selection; existing
  conventions are reused without unrelated replacements.
- Example dependencies, package names, Java/Spring versions, and commands are adapted to
  the actual project. Do not claim tests passed when they were not run.
