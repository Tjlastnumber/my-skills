# Framework-Independent DDD Examples

These Java 8-compatible examples illustrate behavior and boundaries, not required class or
package names. They have no Spring, Lombok, ORM, response-wrapper, or project-exception
dependency. Explicit constructors/getters keep them independently compilable, not a prescribed
style. IDs as strings and simple event payloads are illustrative choices.

## Contents

- [Value Object](#value-object)
- [Domain Event](#domain-event)
- [Aggregate Root](#aggregate-root)
- [Repository Contract](#repository-contract)
- [Domain Service Decision](#domain-service-decision)
- [Standalone Domain Test](#standalone-domain-test)

Each public type below belongs in its own named `.java` file. The package is illustrative.

## Value Object

`FeatureName.java`:

```java
package com.example.project.backend.domain.feature;

public final class FeatureName {
    private static final int MAX_LENGTH = 100;
    private final String value;

    private FeatureName(String value) {
        this.value = value;
    }

    public static FeatureName of(String value) {
        if (value == null || value.trim().isEmpty() || value.length() > MAX_LENGTH) {
            throw new IllegalArgumentException("Invalid feature name");
        }
        return new FeatureName(value);
    }

    public String getValue() {
        return value;
    }

    @Override
    public boolean equals(Object other) {
        return this == other || (other instanceof FeatureName
                && value.equals(((FeatureName) other).value));
    }

    @Override
    public int hashCode() {
        return value.hashCode();
    }
}
```

## Domain Event

`FeatureCreated.java` is a snapshot, not a reference to mutable aggregate state. Add event
identity/time/version metadata only as needed by the chosen delivery design.

```java
package com.example.project.backend.domain.feature;

public final class FeatureCreated {
    private final String featureId;
    private final String name;

    public FeatureCreated(String featureId, String name) {
        this.featureId = featureId;
        this.name = name;
    }

    public String getFeatureId() {
        return featureId;
    }

    public String getName() {
        return name;
    }
}
```

## Aggregate Root

`Feature.java` exposes behavior, not setters. Creation records a fact; reconstruction checks
stored structure without recording another creation. This simplified model only records
creation events; add other event types if the business needs them.

```java
package com.example.project.backend.domain.feature;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class Feature {
    private final String id;
    private FeatureName name;
    private String description;
    private boolean archived;
    private final List<FeatureCreated> pendingEvents = new ArrayList<>();

    private Feature(String id, FeatureName name, String description, boolean archived) {
        if (id == null || id.trim().isEmpty()) {
            throw new IllegalArgumentException("Feature id is required");
        }
        this.id = id;
        this.name = name;
        this.description = description;
        this.archived = archived;
    }

    public static Feature create(String id, String name, String description) {
        Feature feature = new Feature(id, FeatureName.of(name), description, false);
        feature.pendingEvents.add(new FeatureCreated(id, feature.getName()));
        return feature;
    }

    public static Feature reconstruct(String id, String name, String description, boolean archived) {
        return new Feature(id, FeatureName.of(name), description, archived);
    }

    public void updateInfo(String name, String description) {
        requireActive();
        FeatureName validatedName = FeatureName.of(name);
        this.name = validatedName;
        this.description = description;
    }

    public void archive() {
        requireActive();
        archived = true;
    }

    private void requireActive() {
        if (archived) {
            throw new IllegalStateException("Archived features cannot be changed");
        }
    }

    public String getId() { return id; }
    public String getName() { return name.getValue(); }
    public String getDescription() { return description; }
    public boolean isArchived() { return archived; }

    public List<FeatureCreated> pendingEvents() {
        return Collections.unmodifiableList(new ArrayList<>(pendingEvents));
    }

    public void clearPendingEvents() {
        pendingEvents.clear();
    }
}
```

The application layer should clear pending events only after the selected transactional
mechanism accepts them. This aggregate does not implement event delivery. Repositories should
not cache a mutable aggregate instance across failed transactions without restoring state.

The standard exceptions keep this example standalone. In production, use failures expressive
of business meaning and map them at boundaries; do not globally treat every
`IllegalArgumentException`/`IllegalStateException` as a safe client-facing business error.

## Repository Contract

`FeatureRepository.java` speaks in aggregate terms, not MyBatis/SQL types:

```java
package com.example.project.backend.domain.feature;

import java.util.Optional;

public interface FeatureRepository {
    Optional<Feature> findById(String id);
    void save(Feature feature);
}
```

Persistence mapping, audit metadata, deletion strategy, and query pagination are intentionally
absent. If the project intentionally maps domain objects directly with MyBatis-Plus, see the
optional implementation trade-off in [project-templates.md](project-templates.md#optional-direct-persistence-mapping).

## Domain Service Decision

Before creating a domain service, name the business decision it owns. A rule comparing an
existing portfolio's capacity with a proposed allocation might deserve a policy/service;
loading a feature with `findById(...).orElseThrow(...)` is ordinarily application orchestration.
Do not add a `*DomainService` only to wrap a repository call. Keep any genuine domain policy
free of controllers, transaction annotations, and concrete persistence adapters.

## Standalone Domain Test

`FeatureDomainTest.java` uses only the JDK so the examples can be checked without selecting
a test library. `check` and `expect` throw regardless of the JVM's `-ea` setting. In a real
project, translate these cases into its selected test framework.

```java
package com.example.project.backend.domain.feature;

public final class FeatureDomainTest {
    public static void main(String[] args) {
        Feature feature = Feature.create("id-1", "Initial", "description");
        check("id-1".equals(feature.getId()), "Identity should be preserved");
        check(feature.pendingEvents().size() == 1, "Creation should record one event");
        FeatureCreated created = feature.pendingEvents().get(0);
        expect(UnsupportedOperationException.class, () -> feature.pendingEvents().clear());

        feature.updateInfo("Updated", "new description");
        check("Updated".equals(feature.getName()), "Active feature can change");
        check("Initial".equals(created.getName()), "Event must retain its snapshot");
        expect(IllegalArgumentException.class, () -> feature.updateInfo(" ", "invalid"));
        check("Updated".equals(feature.getName()), "Invalid update must preserve state");

        feature.archive();
        expect(IllegalStateException.class, () -> feature.updateInfo("Other", "blocked"));
        expect(IllegalStateException.class, feature::archive);

        Feature restored = Feature.reconstruct("id-2", "Restored", null, true);
        check(restored.isArchived(), "Reconstruction must preserve archived state");
        check(restored.pendingEvents().isEmpty(), "Reconstruction must not emit creation");
        expect(IllegalArgumentException.class, () -> Feature.create("id-3", null, null));
        expect(IllegalArgumentException.class, () -> Feature.reconstruct("", "Name", null, false));
        expect(IllegalArgumentException.class, () -> FeatureName.of(new String(new char[101])));
        FeatureName left = FeatureName.of("Equal");
        FeatureName right = FeatureName.of("Equal");
        check(left.equals(right) && left.hashCode() == right.hashCode(), "Value equality");
        check(!left.equals(FeatureName.of("Different")), "Different values must differ");

        feature.clearPendingEvents();
        check(feature.pendingEvents().isEmpty(), "Accepted events can be cleared");
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private static void expect(Class<? extends Throwable> type, Runnable operation) {
        try {
            operation.run();
        } catch (Throwable failure) {
            if (type.isInstance(failure)) {
                return;
            }
            throw new AssertionError("Unexpected failure", failure);
        }
        throw new AssertionError("Expected " + type.getSimpleName());
    }
}
```

Save the five Java blocks into their named files in a scratch directory, compile with
`javac -d classes *.java`, then run
`java -cp classes com.example.project.backend.domain.feature.FeatureDomainTest` from that
directory. On a JDK supporting `--release 8`, use it to check Java 8 compatibility too.
This verifies model examples only, not persistence, HTTP, or transactional event delivery.
