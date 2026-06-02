package com.example.project.common.exception;

/**
 * Platform-level service exception.
 *
 * Used for general service-layer failures that don't fit the more specific
 * BizException hierarchy. Typically mapped to HTTP 500 by GlobalExceptionHandler.
 *
 * Copy this class into your project's common package and adjust the package name.
 */
public class ServiceException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    public ServiceException() {
        super("服务异常");
    }

    public ServiceException(String message) {
        super(message);
    }

    public ServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
