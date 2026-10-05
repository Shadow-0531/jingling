# -*- coding: utf-8 -*-
"""🧠 AI引擎积木：DeepSeek（OpenAI兼容格式）
【积木规范】一个 engine 必须提供：
  1. NAME                : 字符串
  2. think(msg, cfg)     : 函数，输入一条消息 dict，返回 AI 的一句话字符串
"""
import json
from urllib import request as ureq

NAME = "deepseek"

def think(msg, cfg):
    """cfg: api_base/api_key/model/system_prompt"""
    title = msg.get("title", "")
    body = (msg.get("body") or "").strip()
    content = f"【{title}】"
    if body:
        content += f"\n\n正文：\n{body}"
    data = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": content},
        ],
        "stream": False,
    }).encode()
    req = ureq.Request(cfg["api_base"], data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + cfg["api_key"])
    with ureq.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"]
