package com.example.project.common.domain;

import java.io.Serializable;

/**
 * Unified API response wrapper.
 *
 * Usage:
 *   R.ok()                 — success, no data
 *   R.ok(data)             — success with data
 *   R.ok(data, "message")  — success with data and message
 *   R.fail("error")        — failure with message (code 500)
 *   R.fail(404, "error")   — failure with custom code and message
 *
 * Copy this class into your project's common package and adjust the package name.
 */
public class R<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    public static final int SUCCESS_CODE = 200;
    public static final int FAIL_CODE = 500;

    private int code;
    private String msg;
    private T data;

    public R() {
    }

    public static <T> R<T> ok() {
        return restResult(null, SUCCESS_CODE, "操作成功");
    }

    public static <T> R<T> ok(T data) {
        return restResult(data, SUCCESS_CODE, "操作成功");
    }

    public static <T> R<T> ok(T data, String msg) {
        return restResult(data, SUCCESS_CODE, msg);
    }

    public static <T> R<T> fail() {
        return restResult(null, FAIL_CODE, "操作失败");
    }

    public static <T> R<T> fail(String msg) {
        return restResult(null, FAIL_CODE, msg);
    }

    public static <T> R<T> fail(int code, String msg) {
        return restResult(null, code, msg);
    }

    private static <T> R<T> restResult(T data, int code, String msg) {
        R<T> r = new R<T>();
        r.setCode(code);
        r.setMsg(msg);
        r.setData(data);
        return r;
    }

    public boolean isSuccess() {
        return this.code == SUCCESS_CODE;
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

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }
}
