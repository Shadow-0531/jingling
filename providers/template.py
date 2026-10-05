# -*- coding: utf-8 -*-
"""📝 数据源积木模板——照着我写，就能接新平台。
用法：拷成 my_source.py，改好下面两处，然后在 config.json 里
  "provider": {"use": "my_source", ...}
注意：seen 可能是 set 也可能是 dict（core.py 传的是 dict），
      为兼容两种，建议用下面的 mark_seen。
"""
NAME = "my_source"

def mark_seen(seen, mid):
    try:
        seen.add(mid)      # set
    except AttributeError:
        seen[mid] = 1      # dict

def poll(cfg, seen):
    """返回新消息列表。cfg=config里provider段；seen=已见id（set 或 dict）。
    return [{"id": "唯一id", "title": "给AI看的一句话", "body": "正文（会被喂给AI，别填成标题）"}]"""
    new = []
    # 1) 去平台拿数据（例：requests.get(...)）
    # 2) for 每条：
    #      mid = 该消息唯一id
    #      if mid in seen: continue
    #      mark_seen(seen, mid)
    #      new.append({"id": mid, "title": f"来自 {x}，主题：{y}", "body": 真正的正文})
    return new
