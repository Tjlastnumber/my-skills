# Project Configuration Reference

This file explains how to adapt the `ddd-spring-boot` skill to a specific project. The skill
itself is generic; the values below vary per project.

## Table of Contents

1. [Build Environment](#build-environment)
2. [Maven Modules](#maven-modules)
3. [Package Names](#package-names)
4. [Common Infrastructure Classes](#common-infrastructure-classes)
5. [Exception Classes](#exception-classes)
6. [BaseEntity Fields](#baseentity-fields)
7. [Domain Base Classes](#domain-base-classes)
8. [Build Script Paths](#build-script-paths)

## Build Environment

| Item | Value (adjust per project) |
|------|---------------------------|
| Java version | Per project (read from `pom.xml` `maven.compiler.source` or `<java.version>`) |
| Maven version | 3.6.3+ |
| Parent POM | Your organization's parent POM |
| Group ID | Your project's group ID |
| `.sdkmanrc` | Optional: pins Java/Maven versions |

## Maven Modules

A typical DDD project may have these modules (adjust to match yours):

| Module | Purpose |
|--------|---------|
| `api` | Shared API contracts and models (optional) |
| `core` | Proxy / gateway / infrastructure-facing service (optional) |
| `backend` | Business / domain / data service |

## Package Names

Adjust to your project's base package:

| Module | Base Package (example) |
|--------|----------------------|
| `api` | `com.example.project.api` |
| `core` | `com.example.project.core` |
| `backend` | `com.example.project.backend` |

## Common Infrastructure Classes

These classes provide unified response wrapping and pagination support. Every project using this
skill needs them. There are two options:

### Option A: Project already has a common library

If your organization provides a common-core library (like `ruoyi-common`, `xxx-common-core`, etc.),
use the classes from there. Map the generic names to your library:

| Class | Generic Package | Purpose |
|-------|----------------|---------|
| `R<T>` | `com.example.project.common.domain.R` | Return wrapper: `R.ok(data)`, `R.fail(code, msg)` |
| `BaseController` | `com.example.project.common.web.controller.BaseController` | Provides `startPage()`, `getDataTable()` |
| `TableDataInfo<T>` | `com.example.project.common.web.page.TableDataInfo` | Paginated response wrapper |
| `ServiceException` | `com.example.project.common.exception.ServiceException` | Platform-level service exception |

### Option B: No common library — use the bundled implementations

Complete, ready-to-use implementations (Java 8 compatible, works on any modern Java) are in `scripts/common-infrastructure/`:

| File | Class |
|------|-------|
| `scripts/common-infrastructure/R.java` | `R<T>` — unified response wrapper |
| `scripts/common-infrastructure/TableDataInfo.java` | `TableDataInfo<T>` — paginated response |
| `scripts/common-infrastructure/BaseController.java` | `BaseController` — pagination base (uses PageHelper) |
| `scripts/common-infrastructure/ServiceException.java` | `ServiceException` — platform exception |

Copy these files into your project's common package and rename the package declarations.
`BaseController` requires `com.github.pagehelper:pagehelper-spring-boot-starter` as a dependency.

## Exception Classes

These live in the project's own exception package (e.g., `com.example.project.backend.exception`):

| Class | Extends | Message | Use When |
|-------|---------|---------|----------|
| `BizException` | `RuntimeException` | "业务异常" | Base business exception |
| `NotFoundException` | `BizException` | custom | Resource not found |
| `DeletedException` | `BizException` | custom | Resource already logically deleted |
| `OperationException` | `BizException` | custom | General operation failure |
| `OperationPermissionException` | `OperationException` | custom | No permission for the operation |
| `AlreadyExistsException` | `RuntimeException` | custom | Resource already exists |
| `GlobalExceptionHandler` | — | — | `@RestControllerAdvice` translating exceptions to `R.fail()` |

The `GlobalExceptionHandler` ties the exception hierarchy to `R.fail()`:

| Exception | HTTP code in R |
|-----------|---------------|
| `NotFoundException` | 404 |
| `OperationException` | 400 |
| `OperationPermissionException` | 403 |
| `BizException` / `ServiceException` | 500 |
| Validation errors (`MethodArgumentNotValidException`) | 400 |

## BaseEntity Fields

Location: `com.example.project.backend.domain.BaseEntity`

| Field | Type | Fill Strategy | Purpose |
|-------|------|---------------|---------|
| `createTime` | `LocalDateTime` | `FieldFill.INSERT` | Record creation time |
| `updateTime` | `LocalDateTime` | `FieldFill.INSERT_UPDATE` | Last update time |
| `createBy` | `String` | `FieldFill.INSERT` | Creator user ID |
| `updateBy` | `String` | `FieldFill.UPDATE` | Last updater user ID |
| `deletedFlag` | `Integer` | `@TableLogic` | Logical delete: 0 = active, 1 = deleted |

## Domain Base Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `AggregateRoot` | `...domain.AggregateRoot` | Marker interface for aggregate roots |
| `BaseEntity` | `...domain.BaseEntity` | Audit fields + logical delete (see above) |
| `DomainEvent` | `...domain.event.DomainEvent` | Abstract base with `eventId` and `occurredOn` |
| `DomainEventPublisher` | `...domain.event.DomainEventPublisher` | Wraps Spring `ApplicationEventPublisher` |

## Build Script Paths

Adjust the script names to match your project:

| Script | Path (example) | Purpose |
|--------|---------------|---------|
| Environment check | `./scripts/ensure-build-env.sh` | Verify Java/Maven versions |
| Maven wrapper | `./scripts/mvn-wrapper.sh` | Runs Maven with project settings |

### Common Build Commands

Replace `./scripts/mvn-wrapper.sh` with your actual Maven wrapper script:

```bash
# Validate environment
./scripts/ensure-build-env.sh

# Run all tests
./scripts/mvn-wrapper.sh test

# Build all without tests
./scripts/mvn-wrapper.sh clean package -DskipTests

# Full install
./scripts/mvn-wrapper.sh clean install

# Test only backend module
./scripts/mvn-wrapper.sh -pl backend -am test

# Test only core module
./scripts/mvn-wrapper.sh -pl core -am test

# Build only api module
./scripts/mvn-wrapper.sh -pl api -am package -DskipTests

# Run backend locally
./scripts/mvn-wrapper.sh -pl backend -am spring-boot:run -Dspring-boot.run.profiles=local

# Run core locally
./scripts/mvn-wrapper.sh -pl core -am spring-boot:run -Dspring-boot.run.profiles=local

# Single test class
./scripts/mvn-wrapper.sh -pl backend -am -Dtest=FeatureApplicationServiceTest test

# Single test method
./scripts/mvn-wrapper.sh -pl backend -am -Dtest='FeatureApplicationServiceTest#shouldCreate' test
```
