package com.example.project.common.web.page;

import java.io.Serializable;
import java.util.List;

/**
 * Paginated response wrapper for list queries.
 *
 * Used together with BaseController.startPage() and BaseController.getDataTable().
 *
 * Copy this class into your project's common package and adjust the package name.
 */
public class TableDataInfo<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    public static final int SUCCESS_CODE = 200;

    private long total;
    private List<T> rows;
    private int code;
    private String msg;

    public TableDataInfo() {
    }

    public TableDataInfo(long total, List<T> rows) {
        this.total = total;
        this.rows = rows;
        this.code = SUCCESS_CODE;
        this.msg = "查询成功";
    }

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

    public List<T> getRows() {
        return rows;
    }

    public void setRows(List<T> rows) {
        this.rows = rows;
    }

    public int getCode() {
        return code;
    }

    public void setCode(int code) {
        this.code = code;
    }

    public String getMsg() {
        return msg;
    }

    public void setMsg(String msg) {
        this.msg = msg;
    }
}
