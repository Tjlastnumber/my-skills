# Architecture Reference

## Table of Contents

1. [Module Structure](#module-structure)
2. [Backend Layering](#backend-layering)
3. [Package Layout](#package-layout)
4. [Inter-Module Dependencies](#inter-module-dependencies)
5. [Core Module](#core-module)

## Module Structure

The project is a Maven multi-module build:

```
<project-root>/
├── api/       — shared API contracts and models (no implementation)
├── core/      — proxy / gateway / Kubernetes-facing Spring Boot service
├── backend/   — business / domain / data Spring Boot service
└── pom.xml    — parent POM
```

**api** is the shared contract module. It defines interfaces (e.g., `KubernetesApi`) and data models
(e.g., `JupyterSession`, `LaunchRequest`) that `core` implements and `backend` consumes. Keep
external API contracts here — never in `backend`. (Class names are illustrative; adapt to your project.)

**core** is a gateway/proxy service. It handles authentication, routing, and Kubernetes API calls.
It implements interfaces from `api`.

**backend** is the main business service. It follows DDD layering internally.

## Backend Layering

```
┌─────────────────────────────────────────────────────────────┐
│  controller                                                 │
│  HTTP adapter. Receives requests, validates, delegates.     │
│  Returns R<T> or TableDataInfo<?>.                          │
├─────────────────────────────────────────────────────────────┤
│  application.service                                        │
│  Use-case orchestration. Manages transactions, publishes    │
│  domain events, converts domain objects to DTOs.            │
│  Contains no business rules.                                │
│                                                             │
│  application.dto                                            │
│  Input/output data structures: *Command, *Query, *View.     │
├─────────────────────────────────────────────────────────────┤
│  domain                                                     │
│  Entities, value objects, domain services, domain events,   │
│  repository interfaces. Business invariants live here.      │
├─────────────────────────────────────────────────────────────┤
│  infrastructure                                             │
│  Repository implementations, MyBatis mappers, third-party   │
│  adapters. Implements domain-defined interfaces.             │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Flow

Dependencies flow **inward only**:

- `controller` → `application.service` → `domain` ← `infrastructure`
- `infrastructure` implements interfaces defined in `domain` (Dependency Inversion).
- `application.service` depends on `domain` interfaces, not `infrastructure` classes.

### What Belongs in Each Layer

**controller** — HTTP concern only:
- Request mapping, path variables, request bodies
- `@Valid` on inputs
- Calling the application service
- Wrapping the response in `R<T>` or `TableDataInfo<?>`

**application.service** — orchestration:
- Transaction management (`@Transactional`)
- Coordinating multiple domain entities and services
- Publishing domain events via `DomainEventPublisher`
- Converting between domain objects and DTOs (private `convertToView()` methods)
- No business rules — those belong in domain entities

**application.dto** — data transfer objects:
- `*CreateCommand` / `*SaveCommand` — input for creating new resources
- `*UpdateCommand` — input for updating existing resources
- `*Query` / `Query*Command` — filter/sort parameters for queries
- `*View` — output/response data for the API consumer
- Group by domain in sub-packages: `dto/workspace/`, `dto/notification/`, etc.

**domain** — business core:
- Aggregate roots (implement `AggregateRoot` marker interface)
- Value objects (e.g., `WorkspaceId`, `WorkspaceName`)
- Domain services (stateless logic that spans entities)
- Domain events (extends `DomainEvent`)
- Repository **interfaces** (e.g., `WorkspaceRepository`)

**infrastructure** — technical details:
- Repository implementations (extend `ServiceImpl<Mapper, Entity>`)
- MyBatis mappers (extend `BaseMapper<T>`)
- Third-party service adapters
- Custom MyBatis type handlers

## Package Layout

For a project with base package `com.example.project.backend`:

```
backend/
├── config/                        # Spring configuration classes
├── constant/                      # Application constants
├── controller/                    # HTTP controllers
│   ├── WorkspaceController.java
│   └── NotificationController.java
├── application/
│   ├── dto/                       # Data transfer objects
│   │   ├── workspace/
│   │   │   ├── CreateWorkspaceCommand.java
│   │   │   ├── UpdateWorkspaceCommand.java
│   │   │   ├── QueryWorkspaceCommand.java
│   │   │   ├── WorkspaceView.java
│   │   │   └── WorkspaceDetailView.java
│   │   └── notification/
│   │       ├── SendNotificationCommand.java
│   │       └── NotificationView.java
│   ├── eventhandler/              # Domain event handlers
│   │   └── WorkspaceEventHandler.java
│   └── service/                   # Application services
│       ├── WorkspaceApplicationService.java
│       └── NotificationApplicationService.java
├── domain/
│   ├── AggregateRoot.java         # Marker interface
│   ├── BaseEntity.java            # Audit fields + logical delete
│   ├── workspace/                 # Workspace aggregate
│   │   ├── Workspace.java         # Aggregate root entity
│   │   ├── WorkspaceMember.java   # Entity within aggregate
│   │   ├── WorkspaceRepository.java  # Repository interface
│   │   └── valueobject/
│   │       ├── WorkspaceId.java
│   │       └── WorkspaceName.java
│   ├── event/
│   │   ├── DomainEvent.java       # Abstract base event
│   │   ├── DomainEventPublisher.java
│   │   └── WorkspaceCreatedEvent.java
│   └── notification/              # Another aggregate
│       ├── Notification.java
│       ├── NotificationRepository.java
│       └── valueobject/
│           └── NotificationTypeEnum.java
├── exception/
│   ├── BizException.java
│   ├── NotFoundException.java
│   ├── OperationException.java
│   ├── OperationPermissionException.java
│   ├── DeletedException.java
│   └── GlobalExceptionHandler.java
├── infrastructure/
│   ├── persistence/
│   │   └── mapper/                # MyBatis mapper interfaces
│   │       ├── WorkspaceMapper.java
│   │       └── NotificationMapper.java
│   └── repository/               # Repository implementations
│       ├── WorkspaceRepositoryImpl.java
│       └── NotificationRepositoryImpl.java
└── utils/                         # Utility classes
```

## Inter-Module Dependencies

```
api ← core (core implements api interfaces)
api ← backend (backend uses api models if needed)
backend does NOT depend on core
core does NOT depend on backend
```

When changing an `api` interface:
1. Update the interface in `api`
2. Update the `core` controller that implements it
3. Update any `backend` code that consumes the model

## Core Module

The `core` module is a gateway/proxy service, not a business service. Its structure differs:

```
core/
├── config/           # Gateway and Kubernetes client config
├── controller/       # Proxy controllers (implement api interfaces)
├── filter/           # Global filters (auth, session)
├── model/            # Internal models
├── service/          # Proxy and auth services
│   └── impl/         # Service implementations
├── support/          # Utility and helper classes
└── template/         # Operation templates (e.g., Kubernetes operations)
```

Key conventions for `core`:
- Controllers implement interfaces from the `api` module
- Uses reactive types (`Mono`, `ServerWebExchange`) where the gateway framework requires it
- Does not follow the same DDD layering as `backend` — it's a thinner proxy layer
