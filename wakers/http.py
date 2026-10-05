# -*- coding: utf-8 -*-
"""⚡ 唤醒器积木：HTTP POST

【积木规范】一个 waker 必须提供：
  1. NAME                : 字符串
  2. wake(payload, cfg)  : 函数，把消息“叫醒”给一个AI/服务，返回结果字符串
"""
import json
from urllib import request as ureq

NAME = "http"


def wake(payload, cfg):
    """cfg: url（被唤醒方的地址）"""
    url = cfg.get("url") or cfg.get("wake_url")
    body = json.dumps(payload, ensure_ascii=False).encode()
    req = ureq.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with ureq.urlopen(req, timeout=15) as r:
            return r.read().decode()
    except Exception as e:
        return f"(wake failed: {e})"
