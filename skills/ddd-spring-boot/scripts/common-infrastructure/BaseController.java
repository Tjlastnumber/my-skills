package com.example.project.common.web.controller;

import com.example.project.common.web.page.TableDataInfo;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;
import java.util.List;

/**
 * Base controller providing pagination support via PageHelper.
 *
 * Usage in controllers:
 *   @GetMapping("/page")
 *   public TableDataInfo<?> paged() {
 *       startPage();
 *       return getDataTable(service.list());
 *   }
 *
 * Pagination parameters are read from the HTTP request:
 *   pageNum  — page number (default 1)
 *   pageSize — page size (default 10)
 *   orderBy  — sort clause, e.g. "createTime desc"
 *
 * Copy this class into your project's common package and adjust the package name.
 */
public class BaseController {

    protected void startPage() {
        HttpServletRequest request = getRequest();
        int pageNum = parseInt(request.getParameter("pageNum"), 1);
        int pageSize = parseInt(request.getParameter("pageSize"), 10);
        String orderBy = request.getParameter("orderBy");
        if (orderBy != null && !orderBy.trim().isEmpty()) {
            PageHelper.startPage(pageNum, pageSize, orderBy);
        } else {
            PageHelper.startPage(pageNum, pageSize);
        }
    }

    protected <T> TableDataInfo<T> getDataTable(List<T> list) {
        PageInfo<T> pageInfo = new PageInfo<T>(list);
        return new TableDataInfo<T>(pageInfo.getTotal(), pageInfo.getList());
    }

    private static HttpServletRequest getRequest() {
        ServletRequestAttributes attrs =
                (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attrs == null) {
            throw new IllegalStateException("No request bound to current thread");
        }
        return attrs.getRequest();
    }

    private static int parseInt(String value, int defaultValue) {
        if (value == null || value.trim().isEmpty()) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(value.trim());
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
}
