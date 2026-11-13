# DDD Spring Boot

DDD 建模与分层设计指南，附带**由用户自行选择的项目约定推荐方案**。
一个 skill 入口，两类文档；使用本 skill 不意味着采用全部项目约定。

DDD modeling and layered design guidance, with opt-in project convention recommendations.
DDD guidance does not require any particular response wrapper, ORM, module layout, or build tool.

## 使用方式 / Usage

1. 从 [SKILL.md](SKILL.md) 进入，先识别目标项目已有结构和约定。
2. 建模与分层任务按需读取 DDD 文档，无须加载项目推荐方案。
3. 优先沿用项目已有约定。缺少相关约定时，先让用户选择是否采用推荐项；可全选、部分选择或不采用。
4. 仅使用已选方案的模板，按项目版本、依赖和接口协议调整，不自动复制基础类或添加依赖。

## 文档导航 / Documents

| 类别 | 文档 | 内容 |
| --- | --- | --- |
| DDD 规范 | [architecture.md](references/architecture.md) | 分层职责、依赖方向、Repository 边界 |
| DDD 规范 | [domain-modeling.md](references/domain-modeling.md) | 聚合、实体、值对象、领域服务、领域事件 |
| DDD 示例 | [domain-templates.md](references/domain-templates.md) | 无框架依赖的 Java 建模示例及领域测试 |
| 可选推荐 | [project-conventions.md](references/project-conventions.md) | DI、DTO、校验、接口、异常、风格和测试选项 |
| 可选配置 | [project-config.md](references/project-config.md) | 模块布局、包名、基础类、审计字段和构建示例 |
| 可选模板 | [project-templates.md](references/project-templates.md) | 已选项目方案的实现示例 |

`scripts/common-infrastructure/` 保持原路径，提供可选的响应、分页与异常基础类。
其中 `BaseController.java` 使用 `javax.servlet`，并非 Spring Boot 3 的直接可用模板；
使用前还需审查分页参数与排序字段的校验。详见项目配置文档。

本 skill 无 Python 依赖。验证以 Markdown 引用、示例一致性和目标项目实际构建/测试为准；
领域示例可用 JDK 单独编译，项目模板需要用户选定的相应依赖。
