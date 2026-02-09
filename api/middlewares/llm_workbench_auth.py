#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Workbench 用户认证中间件
用于从 X-LLM-Workbench-User-ID header 中获取用户 ID
"""

import logging
from flask import request, g
from api import settings
from api.utils.api_utils import get_json_result

# 自定义 header 名称
LLM_WORKBENCH_USER_ID_HEADER = "X-LLM-Workbench-User-ID"
ALLOW_PATH_PREFIXES = ("/apidocs", "/apispec.json", "/flasgger_static", "/v1/system/healthz")


def _should_skip_llm_workbench_auth():
    if request.method == "OPTIONS":
        return True
    for prefix in ALLOW_PATH_PREFIXES:
        if request.path.startswith(prefix):
            return True
    return False


def parse_llm_workbench_user_id():
    """
    从请求头中获取 LLM Workbench 用户 ID
    将 user_id 存入 Flask 的 g 对象中
    """
    if _should_skip_llm_workbench_auth():
        return None
    user_id = request.headers.get(LLM_WORKBENCH_USER_ID_HEADER)
    
    if user_id and user_id.strip():
        g.llm_workbench_user_id = user_id.strip()
        logging.info(f"[LLM-Workbench Auth] 接收到用户 ID: {user_id}")
        return None

    g.llm_workbench_user_id = None
    return get_json_result(
        data=False,
        message="Missing X-LLM-Workbench-User-ID header.",
        code=settings.RetCode.AUTHENTICATION_ERROR,
    )


def get_llm_workbench_user_id():
    """
    获取当前请求的 LLM Workbench user_id
    
    Returns:
        str or None: 用户 ID，如果未设置则返回 None
    """
    return getattr(g, 'llm_workbench_user_id', None)


def register_llm_workbench_auth_middleware(app):
    """
    注册中间件到 Flask app
    
    Args:
        app: Flask 应用实例
    """
    @app.before_request
    def before_request():
        resp = parse_llm_workbench_user_id()
        if resp is not None:
            return resp
    
    logging.info("[LLM-Workbench Auth] 中间件已注册")
