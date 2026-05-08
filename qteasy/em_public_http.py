# coding=utf-8
# ======================================
# File:     em_public_http.py
# Author:   Jackie PENG / qteasy
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-05-07
# Desc:
#   东方财富等公网行情接口共用的 requests 参数与带退避重试的 GET+JSON 解析。
# ======================================

from __future__ import annotations

import json
import logging
import time
from typing import Any, Mapping, Optional, Union

import requests

from qteasy._arg_validators import QT_CONFIG

logger = logging.getLogger(__name__)


def _eastmoney_public_request_extras() -> dict[str, Any]:
    """从 QT_CONFIG 组装 timeout、可选 proxies。

    说明
    ----
    ``trust_env`` 不能作为 ``requests.get()`` / ``Session.request()`` 的关键字参数传入
    官方 ``requests``；是否信任环境代理须设置 ``Session.trust_env``（见 ``_one_get``）。
    """

    timeout = float(QT_CONFIG['em_public_http_timeout'])
    extras: dict[str, Any] = {
        'timeout': timeout,
    }
    proxies = QT_CONFIG['em_public_http_proxies']
    if proxies is not None:
        extras['proxies'] = proxies
    return extras


def eastmoney_public_get_json(
        url: str,
        *,
        params: Optional[Union[Mapping[str, Any], list[tuple[str, Any]]]] = None,
        headers: Optional[Mapping[str, str]] = None,
        cookies: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """对东方财富相关 HTTPS 接口执行 GET 并解析 JSON，失败时按 hist_dnld_* 配置退避重试。

    Parameters
    ----------
    url : str
        完整路径，不含重复 query（由 params 单独传入）。
    params : mapping 或 (key, value) 列表，可选
        查询参数。
    headers : mapping，可选
        请求头。
    cookies : mapping，可选
        Cookie；为 None 时不传 cookies 关键字。

    Returns
    -------
    dict
        响应 JSON 对象。

    Raises
    ------
    requests.RequestException
        最后一次尝试仍失败，或 HTTP 非成功状态。
    json.JSONDecodeError
        响应体非合法 JSON。
    """

    mtries = int(QT_CONFIG['hist_dnld_retry_cnt'])
    mdelay = float(QT_CONFIG['hist_dnld_retry_wait'])
    backoff = float(QT_CONFIG['hist_dnld_backoff'])

    def _one_get() -> dict[str, Any]:
        # 每次请求重新读取 QT_CONFIG，与 configure() 热改一致。
        req_extras = _eastmoney_public_request_extras()
        req_kw: dict[str, Any] = {
            'params': params,
            'headers': headers,
            **req_extras,
        }
        if cookies is not None:
            req_kw['cookies'] = cookies
        with requests.Session() as session:
            session.trust_env = bool(QT_CONFIG['em_public_http_trust_env'])
            resp = session.get(url, **req_kw)
        resp.raise_for_status()
        return resp.json()

    last_exc: Optional[BaseException] = None
    while mtries > 1:
        try:
            return _one_get()
        except (requests.RequestException, json.JSONDecodeError, UnicodeDecodeError) as exc:
            last_exc = exc
            logger.debug(
                    'Eastmoney HTTP GET retry pending (%s attempts left): %s: %s',
                    mtries - 1,
                    type(exc).__name__,
                    exc,
            )
            time.sleep(mdelay)
            mdelay *= backoff
            mtries -= 1
    try:
        return _one_get()
    except BaseException:
        if last_exc is not None:
            logger.debug('Eastmoney HTTP GET failed after retries, last retry error was: %s', last_exc)
        raise
