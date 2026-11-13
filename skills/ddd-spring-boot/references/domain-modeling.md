# DDD Domain Modeling

These are modeling guidelines independent of API wrappers, ORM libraries, Lombok, and
project-specific exception classes. Apply them to the business problem, not as a checklist
of classes to generate. See [domain-templates.md](domain-templates.md) for plain Java examples.

## Aggregates and Entities

- An entity has identity across state changes. An aggregate groups entities/value objects
  whose invariants need a consistency boundary; its root controls external mutations.
- Start from business operations and invariants. Do not equate a table, DTO, or module
  with an aggregate by default.
- Express transitions as behavior (`confirm()`, `addMember(...)`) rather than exposing
  unrestricted setters. Return immutable values or defensive collection views.
- Reference other aggregates by identity when practical; avoid creating a large object
  graph merely to navigate relationships.
- Keep rules that can be enforced within an aggregate there. Coordinate wider workflows
  explicitly through application services, domain policies, or events as appropriate.

## Creation and Reconstruction

Use a constructor, named factory, or builder that makes valid creation explicit. A factory
such as `create(...)` is useful when it expresses intent, allocates an identity, and records
a business event; its exact name is not a DDD requirement.

Reconstruction restores persisted state without replaying creation behavior or generating
new creation events. It is **not** permission to accept corrupt state: retain structural
checks and deliberate handling of legacy data, while avoiding checks that belong only to
new operations (for example, "the current user may create an order").

Persistence annotations, audit base classes, ID generation, and logical-delete fields are
project choices. Keep them out of framework-independent examples. Do not automatically
remove them from an existing project that has intentionally selected direct entity mapping.

## Value Objects

Value objects describe a concept by value rather than identity. They can contain one or
multiple fields (e.g. a name, money with currency, or a date range).

- Validate the concept's invariants on construction and keep the result immutable.
- Implement value equality and consistent hash codes.
- Prefer meaningful concepts over wrappers for every primitive. Normalize values only
  when business semantics call for it.
- Validate domain invariants even when HTTP DTO annotations perform similar input checks;
  the domain can also be called by jobs, event handlers, or other adapters.

## Domain Services

Use a domain service for business behavior that does not naturally belong to an entity or
value object, such as a policy involving multiple aggregates. It should express business
language and normally be stateless.

A convenience `findOrThrow(...)` method is not, by itself, a reason to introduce a domain
service. Put loading, saving, transactions, and HTTP concerns in their proper roles. If a
domain policy needs external information, depend on a domain-facing contract, not a mapper
or HTTP client. Whether the service is wired as a Spring bean is a project choice.

## Domain Events and Delivery

Events express facts that have happened, using past-tense names such as `WorkspaceCreated`.
Prefer immutable payloads containing relevant identities/values over references to mutable
aggregate objects. Event metadata such as identity and occurrence time should fit the
target project's needs; UUID and `LocalDateTime` are examples, not requirements.

The aggregate can collect pending events while the application arranges delivery. Distinguish:

1. Recording an event inside the model.
2. Registering it with transactional infrastructure.
3. Executing a handler or delivering a message after a successful commit.

A call to Spring's `publishEvent(...)` does not by itself guarantee post-commit handling.
Use a verified transaction-aware listener or a transactional outbox when required. Rollback
must not produce an externally visible successful business event. Post-commit listeners do
not guarantee durable delivery across process crashes; use an outbox/retry design when the
use case needs that guarantee. Clear pending events only after the chosen mechanism has
accepted them, and consider handler idempotency.

## Errors and Tests

The domain should communicate business failures without HTTP response types or transport
codes. Specific exception names and business-code schemes are optional project choices;
translate failures at the relevant adapter boundary.

Test valid creation, rejected invalid values, allowed/rejected transitions, identity/value
semantics, collection encapsulation, and reconstruction without creation events. Test the
chosen transaction/event-delivery mechanism separately at its integration boundary. Neither
JUnit nor Mockito is required by DDD; follow the project's selected test stack.
