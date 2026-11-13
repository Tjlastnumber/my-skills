---
name: java-best-practices
description: |
  通用 Java 编码最佳实践，涵盖 Controller 映射与 DTO/VO、强制枚举、批量 SQL、
  对象封装、构造器注入及日志记录。编写、修改或审查 Java 代码时使用，包括新增类、接口、
  DTO、实体、Service、Controller，以及重构和修复 bug。
  即使用户没有明确提到“规范”或“最佳实践”，涉及这些 Java 代码变更时也应参照本 skill。
  不预设业务架构；Spring Controller 和依赖注入遵守文中的强制约束，OpenAPI 说明按工具适用。
---

# Java 最佳实践

本指南适用于不同业务领域和架构的 Java 项目。先检查目标项目的 Java 版本、依赖、
代码风格和已有约定，再选择适用的建议；不要仅为遵循示例而引入新框架或分层。
下文明确标记的强制约束优先于一般性建议。Spring 管理的组件统一使用 Lombok
`@RequiredArgsConstructor` 注入；若依赖或注解处理尚未配置，先补齐配置，不退回字段注入。

示例用于展示原则，不代表必须采用的业务模型或目录结构。沿用目标项目的包结构，
将类型和常量放在其所属模块附近，仅在确有共享需求时提取公共定义。

---

## 1. 避免魔法值，合理使用枚举和常量

需要治理的是含义不清、容易误写或难以一致维护的值，而不是所有字符串字面量。
日志模板、一次性的局部提示、注解描述等可以保留在使用处；不要为每个字面量创建常量。

### 1.1 有限取值集合 → 枚举

**强制约束：状态、类型字段必须定义并使用枚举类，禁止使用裸 `0/1/2` 等数字或字符串表达业务含义。**
业务模型和业务逻辑使用枚举类型，不以 `status == 1`、`type.equals("2")` 等方式判断。
如果接口或数据库必须保留数字、字符串编码，应在边界通过枚举的显式 `code` 和转换方法映射，
不改变既有协议，也不把裸编码继续传递到业务逻辑中。
用户可配置、动态扩展的分类应另行建模为分类标识或引用，不能将固定状态伪装成动态分类以绕过枚举约束。

**替换前：**

```java
if ("ACTIVE".equals(status)) {
    // ...
}
```

**替换后：**

```java
public enum Status {
    ACTIVE,
    INACTIVE
}

// 内部模型使用枚举类型
if (status == Status.ACTIVE) {
    // ...
}
```

外部协议或数据库需要稳定字符串编码时，可以为枚举定义显式的 `code` 和转换方法。
先检查现有协议、序列化及持久化逻辑，不要假设枚举常量名就是外部编码，
也不要持久化易随声明顺序变化的 `ordinal()`。对未知值的处理应明确，不能静默映射成无关状态。

### 1.2 稳定且有复用价值的值 → 常量

对重复使用、具有明确含义或需要统一维护的值使用命名常量。
单个类私用的常量保持 `private`；只有确需共享时才扩大可见性。
避免创建收纳所有模块内容的全局 `Constants` 类。

```java
public final class PageLimits {
    private PageLimits() {}

    public static final int DEFAULT_PAGE_SIZE = 20;
    public static final int MAX_PAGE_SIZE = 100;
}
```

不同性质的值使用不同机制：

- 有限状态或类型：枚举。
- 稳定的程序内规则：命名常量。
- 随部署环境变化的地址、超时、开关：配置。
- 密码、密钥、令牌：安全配置或密钥管理机制，不要硬编码。
- 需要国际化的消息：资源文件或项目已有的消息机制。

提取常量时保持原有语义，不要因为多个字符串内容相同，就将不同业务含义强行合并。

### 1.3 校验消息

若项目使用 Jakarta Bean Validation 或兼容的校验机制，可按需求选择：

```java
// 简单且仅在此处使用的消息，可以就近定义
@NotBlank(message = "名称不能为空")
private String name;

// 需要国际化或集中维护时，使用消息资源键
@NotBlank(message = "{user.name.required}")
private String name;
```

上面是两种替代写法，不应同时用于同一字段。使用资源键时，在项目实际使用的消息资源中
配置对应文本。若多个位置确实需要共享同一消息，也可引用字符串常量；注解属性引用的
字段必须是编译期常量，仅声明为 `static final String` 并不保证满足条件。

---

## 2. 说明枚举型 API 参数的合法值

本节适用于使用 OpenAPI/Swagger 的项目。其他项目使用已有的 API 文档机制表达同样的信息，
不必为此引入文档依赖。

请求参数无论声明为 Java 枚举还是表示枚举编码的 `String`，都应让调用方能够查到
合法值及其含义。先检查请求绑定、枚举转换、Jackson 配置和既有接口协议，确保文档与实际行为一致。

### 2.1 请求体 DTO 字段

对于字符串编码，可以使用 `@Schema` 明确取值：

```java
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(
        description = "优先级：LOW-低，MEDIUM-中，HIGH-高",
        allowableValues = {"LOW", "MEDIUM", "HIGH"}
)
private String priority;
```

字段直接声明为枚举时，可由文档工具推导取值，但仍需补充有意义的描述：

```java
@Schema(description = "优先级：LOW-低，MEDIUM-中，HIGH-高")
private Priority priority;
```

如果工具已经正确生成取值列表，避免无必要地重复维护；若显式填写 `allowableValues`，
应与实际接口值同步更新，并检查最终生成的文档。

### 2.2 路径参数和查询参数

在 Spring MVC 项目中，可用 `@Parameter` 和内嵌 `@Schema` 描述查询参数或路径参数：

```java
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Schema;

@GetMapping("/users")
public List<UserVO> findUsers(
        @Parameter(
                description = "状态：ACTIVE-启用，INACTIVE-停用",
                schema = @Schema(allowableValues = {"ACTIVE", "INACTIVE"})
        )
        @RequestParam String status) {
    // 查询逻辑省略
}
```

代码仅展示参数声明。`@Schema` 描述不会代替运行时校验：字符串参数仍需通过项目已有机制
验证或转换，非法值应按接口约定返回明确错误。

### 2.3 避免的问题

- 不要只写“状态枚举”或“详见枚举类”，而不提供调用方可访问的取值说明。
- 不要默认 Java 枚举常量名就是接口值。
- 不要遗漏使用 `String` 接收的枚举编码。
- 修改枚举或转换逻辑时，同步检查文档和相关测试。

---

## 3. 保持对象封装，按需使用访问器和 Lombok

先确定对象是否需要可变、哪些属性应暴露，再选择访问器实现方式。
手写方法、IDE 生成的方法和 Lombok 都可以使用，优先保持项目风格一致。
不要仅为减少代码行数而扩大对象的可变性。

### 3.1 业务对象

包含业务规则的对象，通过表达意图的方法修改状态，避免为所有字段开放 setter。

```java
public final class User {
    private boolean active;

    public boolean isActive() {
        return active;
    }

    public void activate() {
        this.active = true;
    }
}
```

在项目已采用 Lombok 时，可用 `@Getter` 替代适当的 getter，但不要无差别生成 setter。
重建对象优先考虑构造器、静态工厂或受控的映射机制；框架有特殊要求时，
按其实际需要提供构造器和访问方式，而不是默认开放所有属性。

### 3.2 DTO 和持久化对象

- 根据框架的绑定、序列化、代理和持久化要求选择可变或不可变设计，不要假定所有框架都需要 setter。
- Java 版本和框架支持时，可考虑用 `record` 表达不可变的数据载体。
- 使用 Lombok 时，按需选择 `@Getter`、`@Setter`、`@Builder` 等注解。
- 使用 `@Data` 前，确认自动生成的访问器、`toString()`、`equals()` 和 `hashCode()` 都符合需求。
- 对持久化实体尤其谨慎：关联关系、延迟加载和标识变化可能影响相等性、日志输出及性能。
- 避免生成会泄露敏感字段的 `toString()`，也不要通过 getter 暴露可变集合等内部状态。

### 3.3 依赖注入

**强制约束：Spring 管理的 Controller、Service、Repository 等组件，统一使用
`@RequiredArgsConstructor` + `private final` 依赖字段。禁止使用 `@Autowired` / `@Resource`
进行注入，包括字段、方法或构造器上的注入注解。**

```java
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
}
```

确保 Lombok 依赖及注解处理已配置，生成的构造器能够正确解析依赖。存在多个同类型 Bean 时，
使用明确的限定策略，并验证限定信息能出现在生成的构造器参数上，不改用字段注入。
不使用依赖注入框架的普通 Java 对象仍通过显式构造器传入依赖，无需添加 Spring 注解。

---

## 4. 记录有用、适量且安全的日志

沿用项目现有的日志接口和配置。以下以 SLF4J 为例；项目已采用 Lombok 时可用 `@Slf4j`，
否则显式声明 logger 即可，不为日志功能单独引入 Lombok。

### 4.1 在有诊断价值的边界记录

按需要记录关键操作结果、外部调用失败、异常恢复和重要状态变化，而不是给每个类或方法
机械添加日志。检查已有的请求日志、过滤器、切面及异常处理器，避免重复记录。

DTO 等数据载体通常不需要 logger。日志应放在最能提供操作上下文的位置；
业务模型是否依赖日志框架，遵循项目架构约定。

### 4.2 日志级别

| 级别 | 使用场景 |
|---|---|
| `info` | 值得在正常运行中关注的关键事件或操作结果 |
| `warn` | 可恢复但需要关注的异常情况、降级或潜在问题 |
| `error` | 操作失败且需要排查的系统错误或不可预期异常 |
| `debug` | 开发调试与诊断细节，通常不在生产默认开启 |

正常的业务拒绝、取消或输入校验失败不必一律记为 `warn`，应根据影响和运维需要决定。
捕获异常也不意味着必须记为 `error`，先判断其是否预期、是否已处理，以及是否会在上层重复记录。

### 4.3 日志写法

```java
private static final Logger log = LoggerFactory.getLogger(UserService.class);

// 使用稳定标识定位操作，避免记录完整请求或对象
log.info("用户已启用, userId={}", userId);

// 需要记录异常时，保留堆栈和必要上下文；异常本身也可能包含敏感数据
log.error("用户更新失败, userId={}", userId, exception);
```

- 使用参数化日志，避免字符串拼接。SLF4J 使用 `{}` 占位符。
- 不记录密码、令牌、密钥和未经处理的个人敏感信息；对必要字段进行脱敏。
- 对用户输入进行适当处理，防止换行等内容伪造日志记录。
- 避免循环中的高频 `info` 日志，优先汇总；高频 `debug` 日志也应控制数量和开销。
- 参数化日志不会阻止参数表达式求值，昂贵的计算应使用级别判断或日志框架支持的惰性求值。
- 使用项目已有的请求或追踪标识关联日志，不要到处重复记录同一异常。
- 事务提交前的日志不能证明数据已提交；需要确认提交结果的事件，应在提交后记录或发布。

---

## 5. Controller、DTO 与 VO 强制约束

### 5.1 显式 HTTP 方法和完整路径

- 禁止使用 `@RequestMapping`，包括类级路径前缀和方法级映射。
- 每个处理方法使用 `@GetMapping`、`@PostMapping`、`@PutMapping`、`@PatchMapping`
  或 `@DeleteMapping` 等与实际 HTTP 语义匹配的专用注解。
- 在方法注解中写完整路径，不依赖类级映射拼接；这里的完整路径指应用内接口路径，
  不包含域名、部署上下文路径或网关前缀。

### 5.2 类型明确的入参和响应

- Controller 收参禁止使用 `Map`，包括请求体、查询参数聚合、嵌套 DTO 中用于替代明确字段的 Map。
  使用明确的标量、枚举或 DTO 表达请求结构。
- 单个接口的业务入参超过 4 个字段时，必须使用 DTO；按请求实际字段计数，
  不能通过嵌套、集合包装或拆成多个方法参数规避。路径中的资源标识仍用 `@PathVariable` 表达，
  其余请求字段通过 DTO 绑定；JSON 请求体使用 `@RequestBody`，查询表单使用适当的对象绑定方式。
- DTO 每个字段必须通过注释写清业务含义和取值范围，包括适用的长度、上下界、单位、
  枚举值、必填性或格式要求；使用 OpenAPI 时同步提供对应文档，并通过校验或转换落实限制。
- Controller 禁止直接返回 Entity 或持久化对象，必须转换为专用 VO（View Object）。
  集合、分页结果和统一响应包装内部也不得包含 Entity；无响应体接口可以返回 `void`。
- DTO 用于接收请求，VO 用于响应，仅暴露接口需要的字段；不要直接把持久化对象改名为 VO。

```java
@RestController
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;
    private final UserConverter userConverter;

    @GetMapping("/users/{id}")
    public UserVO getUser(@PathVariable("id") Long id) {
        return userConverter.toVO(userService.findById(id));
    }
}
```

示例中的转换器由项目实现并注册为 Bean，VO 应独立定义。DTO 字段文档示例：

```java
/** 显示名称；必填，去除首尾空白后长度为 1–50 个字符。 */
@NotBlank
@Size(min = 1, max = 50)
private String name;

/** 年龄；选填，单位为岁，范围为 0–150。 */
@Min(0)
@Max(150)
private Integer age;
```

校验前按约定完成空白处理，并在 Controller 绑定 DTO 时启用 `@Valid` / `@Validated`；
注释不替代运行时校验，校验注解也不应与实际处理顺序矛盾。

---

## 6. 批量数据库操作强制约束

**批量操作一律使用批处理，禁止在 `for` / `while` 循环中逐条调用 SQL。**
同样禁止通过 `forEach`、Stream、递归、异步任务或循环调用 Service 等方式间接逐条执行 SQL。

- 批量查询使用集合条件、关联查询或框架提供的批量读取能力，避免逐条查询和 N+1。
- 批量新增、更新和删除使用多行 SQL、集合条件或实际启用的 JDBC/ORM 批处理能力，
  不以方法名包含 `batch` 作为已满足约束的证明。
- 集合转换、内存校验可以循环执行，但循环内部及其调用链不得逐条访问数据库。
- 数据量较大时允许按数据库参数上限和内存限制分块，每块执行集合 SQL 或真正的批处理；
  不能将分块大小固定为 1 来规避要求。
- 明确事务边界、失败处理及批次结果；检查框架配置和实际 SQL 执行，确认批处理生效。

```java
// 禁止：逐条查询，即使藏在 Service 方法内部也不允许
for (Long id : ids) {
    userRepository.findById(id);
}

// 推荐：一次集合查询；必要时按合理大小分块
List<User> users = userRepository.findAllByIds(ids);
```

示例方法名仅表示意图，具体实现需验证是集合查询，而非循环调用单条查询。

---

## 检查清单

编写或修改 Java 代码后，按实际适用范围检查：

- [ ] 遵循目标项目的 Java 版本、依赖、包结构和现有约定，没有引入不必要的技术栈或分层
- [ ] 含义不清的魔法值已通过枚举、常量或配置合理表达，没有机械提取所有字面量
- [ ] 枚举与外部协议、序列化和持久化逻辑一致，未知值的处理明确
- [ ] 状态、类型字段已定义枚举，业务逻辑中没有裸 `0/1/2` 或字符串编码判断
- [ ] 校验消息按复用或国际化需求处理，而非强制引用常量
- [ ] 若存在 API 文档，枚举型参数的合法值和含义与实际行为一致，且有运行时校验或转换
- [ ] 访问器、可变性和相等性符合对象职责，没有无意暴露内部状态
- [ ] Lombok 生成的行为符合需求；Spring 组件使用 `@RequiredArgsConstructor` + `private final`，没有 `@Autowired` / `@Resource`
- [ ] Controller 未使用 `@RequestMapping`，每个接口使用 HTTP 专用映射注解并声明完整路径
- [ ] Controller 收参没有 Map；入参超过 4 个字段时使用 DTO，字段注释明确含义和取值范围
- [ ] Controller 返回专用 VO，集合、分页和响应包装内也没有直接暴露 Entity
- [ ] 批量操作使用集合 SQL 或真实批处理，没有循环及其调用链中的逐条 SQL；分块大小合理
- [ ] 日志有诊断价值、级别恰当、无重复和敏感信息泄露风险
- [ ] 使用目标项目已有的编译、测试或静态检查方式验证变更；不适用的条目标为不适用
