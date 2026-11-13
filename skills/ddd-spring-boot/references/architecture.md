# DDD Architecture Reference

This document describes responsibilities and dependency boundaries, not a mandatory package
or Maven module layout. Names such as `controller` and `application` identify roles;
map them to the target project's existing structure.

## Layer Responsibilities

| Role | Responsibility | Keep out |
| --- | --- | --- |
| Interface adapter (e.g. HTTP controller) | Translate requests, validate transport input, call use cases, translate results/errors | Business state transitions and persistence access |
| Application service | Orchestrate use cases, load/save aggregates through ports, define transaction boundaries, coordinate event dispatch | Business invariants that belong to the domain |
| Domain | Aggregates, entities, value objects, domain services, domain events, business-facing repository contracts | HTTP response wrappers, controller types, ORM query builders, transport status codes |
| Infrastructure | Implement repositories and external-service ports; handle persistence, messaging, and third-party APIs | Owning business rules merely because it has access to stored data |

## Dependency Direction

```text
interface adapters → application → domain ← infrastructure
```

- Application services depend on domain contracts rather than concrete repository adapters.
- Infrastructure implements inward-facing interfaces (dependency inversion).
- Runtime calls can reach infrastructure through those interfaces; this does not mean
  domain code imports infrastructure implementations.
- Wiring belongs at the composition boundary. Spring bean annotations, module names, and
  package locations are implementation choices, not the definition of a layer.
- A small project can express these boundaries within one module. Additional modules
  are useful only when they support actual isolation or deployment needs.

## Application vs Domain Logic

An application service might load an order, call `order.confirm()`, persist it, and arrange
event delivery. Whether the order can be confirmed belongs in the order's behavior or a
domain policy, not in controller conditionals or a database mapper.

Transactions normally enclose the use case. Choose their actual scope with the aggregate
consistency requirements and target infrastructure in mind; annotations alone do not define
the business boundary. Avoid introducing distributed transactions merely to join aggregates.

Request DTOs and response models belong at application/interface boundaries according to
the project's design. The domain should not need them to enforce its rules. Naming them
`*Command`, `*Query`, or `*View` is an optional project convention.

## Repository and Integration Boundaries

- Define repository contracts in domain terms, normally around aggregate roots rather
  than one repository per table. Keep SQL, mapper types, pagination plugins, and persistence
  entities out of those contracts.
- Reconstitute aggregates through the chosen mapping strategy. A separate persistence
  model is useful for isolation but is not mandated for every existing project.
- Model third-party access as a port when the domain/application needs a capability;
  implement protocol details in an adapter. Translate external failures at that boundary.
- Read-only query projections can use a dedicated query path without loading full
  aggregates. They must not become a back door for bypassing write-side invariants.

## Cross-Layer Change Review

When changing a use case, inspect the relevant domain behavior, repository contract,
application flow, DTO/API contract, adapter implementation, and tests. Change only what the
use case requires; do not manufacture empty layers or refactor unrelated modules.

For aggregate and event details, see [domain-modeling.md](domain-modeling.md). For an
**optional** `api/core/backend` layout and concrete package examples, see
[project-config.md](project-config.md); that layout is not part of this DDD guidance.
