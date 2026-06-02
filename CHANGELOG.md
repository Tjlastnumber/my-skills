# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-02

### Added
- `ddd-spring-boot` skill：DDD 风格 Spring Boot 项目分层约定（controller → application.service → domain → infrastructure），含 Maven/Java 配置、代码模板与单元测试约定，以及 `common-infrastructure` 通用基础类（`BaseController`、`R`、`ServiceException`、`TableDataInfo`）
- `mybatis-plus-persistence` skill：MyBatis-Plus 持久层约定，覆盖 Mapper/Repository 实现、实体映射注解、Wrapper 查询、BaseEntity 审计字段与逻辑删除
- `database-design` skill：数据库设计规范与变更指南，提供 MySQL/PostgreSQL 双方言 DDL 模板、命名与列规范、枚举/类型策略、迁移脚本与变更检查清单

### Changed
- 根目录 `README.md` 的 Current Skills 表登记 `ddd-spring-boot`、`mybatis-plus-persistence`、`database-design` 三个新 skill

## [0.1.0] - 2025-05-25

### Added
- `prd-writer` skill：两阶段引导式 PRD 生成，三视角需求诊断 + 概念版/落地版流程 + 四大盲区自检

### Changed
- `AGENTS.md` 补充仓库结构说明、新增 skill 流程、现有 skill 使用方式和约定

## 0.0.1 - 2025-04-25

### Added
- 初始化仓库
- `markdown-to-word` skill：基于模板的 Markdown → DOCX 转换流程

[Unreleased]: https://github.com/user/my-skills/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/user/my-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/user/my-skills/compare/0.0.1...v0.1.0
