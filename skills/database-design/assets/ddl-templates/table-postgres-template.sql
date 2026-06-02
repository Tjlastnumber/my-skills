-- ============================================================
-- PostgreSQL 建表模板
-- 使用前替换：<prefix>、<table_name>、<TableComment>、业务列
-- ============================================================

CREATE TABLE <prefix>_<table_name> (
    id              VARCHAR(128)   NOT NULL,

    -- ========== 业务列（按逻辑分组排列） ==========
    -- 示例：
    -- name            VARCHAR(255)   NOT NULL,
    -- description     VARCHAR(1024)  DEFAULT NULL,
    -- status          VARCHAR(32)    DEFAULT NULL,
    -- project_id      VARCHAR(128)   DEFAULT NULL,
    -- labels          JSON           DEFAULT NULL,

    -- ========== 标准审计列（不可省略，顺序固定） ==========
    create_time     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    update_time     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    create_by       VARCHAR(128)   DEFAULT NULL,
    update_by       VARCHAR(128)   DEFAULT NULL,
    deleted_flag    INT            DEFAULT 0,

    -- ========== 约束 ==========
    PRIMARY KEY (id)
);

-- ========== 索引（替换为实际的列名） ==========
-- CREATE INDEX idx_<table_name>_<col> ON <prefix>_<table_name> (<col>);

-- ========== 注释 ==========
COMMENT ON TABLE <prefix>_<table_name> IS '<TableComment>';
COMMENT ON COLUMN <prefix>_<table_name>.id IS '主键ID';
-- COMMENT ON COLUMN <prefix>_<table_name>.name IS '名称';
-- COMMENT ON COLUMN <prefix>_<table_name>.description IS '描述';
-- COMMENT ON COLUMN <prefix>_<table_name>.status IS '状态';
-- COMMENT ON COLUMN <prefix>_<table_name>.project_id IS '关联项目ID';
COMMENT ON COLUMN <prefix>_<table_name>.create_time IS '创建时间';
COMMENT ON COLUMN <prefix>_<table_name>.update_time IS '更新时间';
COMMENT ON COLUMN <prefix>_<table_name>.create_by IS '创建人';
COMMENT ON COLUMN <prefix>_<table_name>.update_by IS '更新人';
COMMENT ON COLUMN <prefix>_<table_name>.deleted_flag IS '逻辑删除标识: 0=正常, 1=已删除';
