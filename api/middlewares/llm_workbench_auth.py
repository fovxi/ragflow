#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Workbench 用户认证中间件
用于从 X-LLM-Workbench-User-ID header 中获取用户 ID
"""

import logging
from flask import request, g

# 自定义 header 名称
LLM_WORKBENCH_USER_ID_HEADER = "X-LLM-Workbench-User-ID"


def parse_llm_workbench_user_id():
    """
    从请求头中获取 LLM Workbench 用户 ID
    将 user_id 存入 Flask 的 g 对象中
    """
    user_id = request.headers.get(LLM_WORKBENCH_USER_ID_HEADER)
    
    if user_id and user_id.strip():
        g.llm_workbench_user_id = user_id.strip()
        logging.info(f"[LLM-Workbench Auth] 接收到用户 ID: {user_id}")
    else:
        # 如果没有提供 user_id，设为 None（用于兼容旧的 ragflow 自身的请求）
        g.llm_workbench_user_id = None
        logging.debug("[LLM-Workbench Auth] 未提供用户 ID，使用 ragflow 默认认证")


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
        parse_llm_workbench_user_id()
    
    logging.info("[LLM-Workbench Auth] 中间件已注册")

