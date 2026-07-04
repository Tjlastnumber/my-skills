---
name: java-best-practices
description: |
  oo-tms-agg 项目的 Java 编码规范。在编写或修改本项目中任何 Java 代码时都应遵循本规范，
  包括新增类、修改已有类、生成 DTO/Entity/Service/Controller 等。
  当用户要求"写一个新接口"、"添加一个 Service"、"创建实体类"、"重构代码"、
  "修复 bug"、"添加字段"等涉及 Java 代码变更的操作时，使用本 skill。
  即使用户没有明确提到"规范"或"最佳实践"，只要涉及 Java 代码编写，就应参照本 skill。
---

# oo-tms-agg Java 编码规范

本规范针对 oo-tms-agg 项目（Java 17 + Spring Boot 3.3 + MyBatis-Plus + Lombok）。

---

## 1. 字符串禁止硬编码

任何在代码逻辑中使用的字符串值，不得以字面量形式直接写在业务逻辑里。按以下两种方式处理：

### 1.1 魔法字符串 → 枚举

**魔法字符串**指的是有固定取值集合、代表某种状态/类型/节点的字符串，例如状态码、节点代码、业务类型标识。

**识别特征**：同一个字符串值在多处出现，或者它代表一个有限的、可穷举的集合。

**做法**：定义枚举类，使用枚举常量替代字符串字面量。枚举类放在对应限界上下文的 `domain/<context>/model/` 包下。

**示例 — 替换前：**
```java
// Task.java — 到处散落 "START", "DONE"
task.currentNode = "START";
this.currentNode = "DONE";

// ApprovalInstance.java
this.currentNodeCode = "DONE";

// MockWorkflowEngineGateway.java
"CENTER_LEADER", "DEPT_MANAGER", "EXECUTOR"
```

**示例 — 替换后：**
```java
// domain/shared/model/WorkflowNode.java — 工作流节点是跨上下文的共享概念
public enum WorkflowNode {
    START("START", "起始"),
    CENTER_LEADER("CENTER_LEADER", "中心领导审批"),
    DEPT_MANAGER("DEPT_MANAGER", "室主任审批"),
    EXECUTOR("EXECUTOR", "执行人接收"),
    DONE("DONE", "已结束");

    private final String code;
    private final String label;

    WorkflowNode(String code, String label) {
        this.code = code;
        this.label = label;
    }

    public String getCode() { return code; }
    public String getLabel() { return label; }
}

// Task.java 中使用
task.currentNode = WorkflowNode.START.getCode();
this.currentNode = WorkflowNode.DONE.getCode();
```

对于仅在单一限界上下文内使用的魔法字符串，枚举直接放在该上下文的 model 包下。对于跨上下文共享的（如 WorkflowNode），放在 `domain/shared/model/` 下。

### 1.2 描述性字符串 → 常量类

**描述性字符串**指的是错误消息、提示文本、前缀、分隔符等不具备"有限集合"特征的字符串。

**做法**：在对应限界上下文的 `domain/<context>/` 包下创建 `<Context>Constants.java`，将字符串提取为 `public static final` 常量。

**示例 — 替换前：**
```java
// Task.java
throw new OperationException("退回原因不能为空");
throw new OperationException("当前状态不允许取消");
throw new OperationException("进度必须在 0-100 之间");
throw new OperationException("计划开始时间不能晚于计划结束时间");

// TaskDomainService.java
throw new NotFoundException("任务不存在: " + taskId);

// TaskApplicationService.java
approvalApplicationService.getApprovalSummary("TASK_APPROVAL", createdTask.getId());
```

**示例 — 替换后：**
```java
// domain/task/TaskConstants.java
public final class TaskConstants {

    private TaskConstants() {}

    public static final String REJECT_REASON_REQUIRED = "退回原因不能为空";
    public static final String CANCEL_NOT_ALLOWED = "当前状态不允许取消";
    public static final String PROGRESS_OUT_OF_RANGE = "进度必须在 0-100 之间";
    public static final String DATE_RANGE_INVALID = "计划开始时间不能晚于计划结束时间";
    public static final String STATUS_OPERATION_NOT_ALLOWED = "任务状态为 %s，不允许此操作";
    public static final String TASK_NOT_FOUND = "任务不存在: %s";

    public static final String BUSINESS_TYPE_APPROVAL = "TASK_APPROVAL";
}

// Task.java 中使用
throw new OperationException(TaskConstants.REJECT_REASON_REQUIRED);
throw new OperationException(String.format(TaskConstants.STATUS_OPERATION_NOT_ALLOWED, this.status.getLabel()));
```

### 1.3 各层的处理策略

| 层 | 魔法字符串 | 描述性字符串 |
|---|---|---|
| **domain** | → 枚举（model 包下） | → `*Constants.java`（限界上下文根包下） |
| **application** | 引用 domain 层定义的枚举 | → `*Constants.java`（application 层或引用 domain 层常量） |
| **interfaces**（Controller） | Swagger 注解中的 `@Tag(name=...)`、`@Operation(summary=...)` 可以直接写字符串，这些是 API 文档描述 | 业务逻辑中的字符串走常量 |
| **infrastructure** | 引用 domain 层枚举 | Mock 数据中的占位字符串暂可保留 |

### 1.4 DTO 校验消息

`@NotBlank(message = "...")` 等校验注解中的消息字符串，提取到对应 Constants 类并引用常量：

```java
// 替换前
@NotBlank(message = "任务标题不能为空")
private String title;

// 替换后
@NotBlank(message = TaskConstants.TITLE_REQUIRED)
private String title;
```

注意：`message` 属性要求编译期常量，所以 `TaskConstants` 的字段必须是 `static final String`。

---

## 2. 使用 Lombok 注解替代手写 get/set

本项目的 Lombok 依赖已在 pom.xml 中配置。所有 Java 类应根据所处层级使用恰当的 Lombok 注解，不要手写 getter/setter 方法。

### 2.1 各层 Lombok 注解规范

**领域层 — 聚合根 / 实体：**
- 使用 `@Getter`，不使用 `@Setter`
- 状态变更通过领域方法（如 `submit()`, `approve()`, `reject()`）完成，不暴露 setter
- 领域层追求封装性和不变性

```java
import lombok.Getter;

@Getter
public class Task extends AggregateRoot {
    private String title;
    private TaskStatus status;

    // 状态变更通过领域方法
    public void approve() { this.status = TaskStatus.APPROVED; }
    // 不要写 public void setStatus(TaskStatus s) { ... }
}
```

**领域层 — 值对象 / 需要被 MyBatis Converter 重建的实体：**
- 如果 Converter 需要设置属性（如从 DO 重建 Entity 时），可以用 `@Getter` + `@Setter`
- 但优先考虑通过构造器或静态工厂方法创建，而非暴露 setter

**基础设施层 — DO（Data Object）：**
- 使用 `@Data`（含 getter/setter/toString/equals/hashCode）
- DO 是纯粹的数据搬运对象，没有业务逻辑

```java
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class TaskDO extends BaseDO {
    private String taskNo;
    private String title;
}
```

**应用层 — DTO / Command / View：**
- 使用 `@Data` 或 `@Getter` + `@Builder`
- 入参 Command：`@Data`（框架需要 setter 来绑定参数）
- 出参 View：`@Data`（Assembler 需要逐字段设值）
- 不可变的内部模型：`@Getter` + `@Builder`

```java
import lombok.Data;

@Data
public class TaskCreateCommand {
    @NotBlank(message = TaskConstants.TITLE_REQUIRED)
    private String title;
}

@Getter
@Builder
public static class CreateModel {
    private final String id;
    private final String title;
}
```

**Service / Controller / Repository 实现：**
- 使用 `@RequiredArgsConstructor` 实现构造器注入
- 不使用 `@Autowired` 字段注入

```java
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class TaskApplicationService {
    private final TaskDomainService taskDomainService;
    private final TaskRepository taskRepository;
    // Spring 自动通过构造器注入
}
```

### 2.2 不要做的事

- 不要手写 getter/setter —— 用 Lombok 注解替代。`ApprovalInstance.java` 中 150+ 行手写 getter/setter 就是反面教材，应该用 `@Getter` + `@Setter` 替代。
- 不要在领域聚合根上使用 `@Data` —— 这会暴露 setter，破坏封装性。
- 不要在 DO 上使用 `@Getter` + `@Setter` 代替 `@Data` —— DO 就是要方便地读写所有字段。

---

## 3. 日志规范

本项目当前没有任何日志记录，后续开发应逐步补齐。日志使用 Lombok 的 `@Slf4j` 注解。

### 3.1 哪些类需要日志

| 类 | 使用 @Slf4j | 说明 |
|---|---|---|
| ApplicationService | 是 | 编排逻辑，记录关键业务操作 |
| DomainService | 是 | 领域操作 |
| Controller | 是 | 请求入口，记录请求和响应 |
| Repository 实现 | 是 | 持久化操作（可选，复杂查询时记录） |
| Domain 聚合根/实体 | 否 | 领域模型保持纯粹，不依赖日志框架 |
| DO / DTO | 否 | 纯数据对象 |

### 3.2 日志级别指南

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class TaskApplicationService {

    @Transactional
    public TaskView createTask(TaskCreateCommand cmd) {
        log.info("创建任务, title={}", cmd.getTitle());
        Task task = ...;
        log.info("任务创建成功, id={}, taskNo={}", task.getId(), task.getTaskNo());
        return toView(task);
    }

    @Transactional
    public void rejectTask(String id, String reason, String handlerId) {
        log.warn("任务被退回, id={}, reason={}", id, reason);
        // ...
    }
}
```

| 级别 | 使用场景 |
|---|---|
| `log.info` | 关键业务操作（创建、状态变更、审批动作）的开始和完成 |
| `log.warn` | 业务异常情况（退回、取消、校验不通过） |
| `log.error` | 系统异常、不可预期的错误（try-catch 中捕获的异常） |
| `log.debug` | 开发调试信息，排查问题时使用 |

### 3.3 日志注意事项

- 使用 `{}` 占位符，不要字符串拼接：`log.info("任务创建, id={}", id)` 而非 `log.info("任务创建, id=" + id)`
- 不要记录敏感信息（密码、token）
- 不要在循环中打 info 级别日志，用 debug

---

## 检查清单

编写或修改 Java 代码后，逐项确认：

- [ ] 没有新增字符串字面量直接写在业务逻辑中
- [ ] 魔法字符串已定义为枚举
- [ ] 描述性字符串已提取到 Constants 类
- [ ] DTO 校验消息引用常量
- [ ] 没有手写 getter/setter（使用 Lombok 注解）
- [ ] 聚合根只用了 `@Getter`，没有 `@Setter`/`@Data`
- [ ] Service/Controller 使用了 `@RequiredArgsConstructor` + `@Slf4j`
- [ ] 日志使用 `{}` 占位符，级别恰当
