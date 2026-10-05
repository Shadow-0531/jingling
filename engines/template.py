# -*- coding: utf-8 -*-
"""📝 AI引擎积木模板——照我写，换模型（OpenAI/通义/本地都行）。"""
NAME = "my_engine"

def think(msg, cfg):
    """输入一条消息 dict（含 title 与 body，两个都要用上，别只读 title），
    返回一段字符串。cfg=config里engine段。"""
    title = msg.get("title", "")
    body = (msg.get("body") or "").strip()
    content = f"【{title}】"
    if body:
        content += f"\n\n正文：\n{body}"
    # 调你的API，传入 content，返回 text
    return "（未实现）"
