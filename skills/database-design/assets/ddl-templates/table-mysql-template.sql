-- ============================================================
-- MySQL 建表模板
-- 使用前替换：<prefix>、<table_name>、<TableComment>、业务列
-- ============================================================

CREATE TABLE <prefix>_<table_name> (
    id              VARCHAR(128)   NOT NULL                COMMENT '主键ID',

    -- ========== 业务列（按逻辑分组排列） ==========
    -- 示例：
    -- name            VARCHAR(255)   NOT NULL                COMMENT '名称',
    -- description     VARCHAR(1024)  DEFAULT NULL            COMMENT '描述',
    -- status          VARCHAR(32)    DEFAULT NULL            COMMENT '状态',
    -- project_id      VARCHAR(128)   DEFAULT NULL            COMMENT '关联项目ID',
    -- labels          JSON           DEFAULT NULL            COMMENT '标签列表',

    -- ========== 标准审计列（不可省略，顺序固定） ==========
    create_time     DATETIME       DEFAULT CURRENT_TIMESTAMP              COMMENT '创建时间',
    update_time     DATETIME       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    create_by       VARCHAR(128)   DEFAULT NULL                           COMMENT '创建人',
    update_by       VARCHAR(128)   DEFAULT NULL                           COMMENT '更新人',
    deleted_flag    INT            DEFAULT 0                              COMMENT '逻辑删除标识: 0=正常, 1=已删除',

    -- ========== 约束 ==========
    PRIMARY KEY (id),

    -- ========== 索引（替换为实际的列名） ==========
    -- INDEX idx_<table_name>_<col> (<col>),

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='<TableComment>';
