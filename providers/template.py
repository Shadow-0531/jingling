# -*- coding: utf-8 -*-
"""📝 数据源积木模板——照着我写，就能接新平台。

用法：拷成 my_source.py，改好下面两处，然后在 config.json 里
  "provider": {"use": "my_source", ...}
"""
NAME = "my_source"


def poll(cfg, seen):
    """返回新消息列表。cfg=config里provider段；seen=已见id集合（要把你的id加进去去重）。
    return [{"id": "唯一id", "title": "给AI看的一句话", "body": "正文"}]"""
    new = []
    # 1) 去平台拿数据（例：requests.get(...)）
    # 2) for 每条：
    #      mid = 该消息唯一id
    #      if mid in seen: continue
    #      seen.add(mid)
    #      new.append({"id": mid, "title": f"来自 {x}，内容：{y}", "body": y})
    return new
