# -*- coding: utf-8 -*-
"""📮 数据源积木：邮箱（POP3）
【积木规范】一个 provider 必须提供两个东西：
  1. NAME        : 字符串，本积木的名字
  2. poll(cfg, seen) : 函数，返回“新消息列表” list[dict]
                   每个 dict 至少含 {"id", "title", "body"}
                   没新消息就返回 []
config 里 provider 段会原样传给 poll(cfg, seen)。
"""
import poplib, email, re
from email.header import decode_header

NAME = "mail"

def dh(s):
    if not s:
        return ""
    out = []
    for part, enc in decode_header(s):
        if isinstance(part, bytes):
            try:
                out.append(part.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(part.decode("utf-8", errors="replace"))
        else:
            out.append(part)
    return "".join(out)

def mark_seen(seen, mid):
    """去重兼容层：core.py 传进来的可能是 set，也可能是 dict，两种都接住。"""
    try:
        seen.add(mid)      # 传进来是 set
    except AttributeError:
        seen[mid] = 1      # core.py 实际传的是 dict

def _decode_part(part):
    """取一个 part 的可读文本，自动处理 base64 / quoted-printable / charset。"""
    try:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    except Exception as e:
        print(f"[mail] 解码 part 失败: {e}", flush=True)
        return ""

def _strip_html(t):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"<[^>]+", " ", t)
    import html as _html
    t = _html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()

def get_body(msg, limit=1500):
    """取正文：优先 text/plain -> text/html（去标签）-> 其他可读部分。
    取不到可读内容时，明确返回一句提示，而非空串。"""
    text = ""
    html_text = ""
    try:
        parts = list(msg.walk()) if msg.is_multipart() else [msg]
        for part in parts:
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            if ctype == "text/plain":
                t = _decode_part(part)
                # 去除引用符号(>)和空白后，如果几乎没内容，视为无效（有些邮件 text/plain 只有空引用）
                if len(re.sub(r"[>\s]+", "", t)) >= 2:
                    text = t
                    break
            elif ctype == "text/html":
                t = _decode_part(part)
                if t.strip() and not html_text:
                    html_text = t
        if not text.strip():
            text = _strip_html(html_text) if html_text else ""
    except Exception as e:
        print(f"[mail] 取正文失败: {e}", flush=True)
        return ""
    # 清理：有些 HTML 去标签后会剩一堆引用/表格符号(>)与孤立符号，全清掉
    text = re.sub(r"[>　]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # 清理后如果只剩符号/空白（可读字符太少），判为无正文
    readable = re.sub(r"[\W_]+", "", text, flags=re.UNICODE)
    if len(readable) < 15:
        return "（这封信没有可读正文，可能只有样式/图片）"
    return text[:limit]
def poll(cfg, seen):
    """cfg: pop_host/pop_port/user/pass/scan_last；seen: set 或 dict（已见id）"""
    P = poplib.POP3_SSL(cfg["pop_host"], cfg["pop_port"], timeout=40)
    P.user(cfg["user"])
    P.pass_(cfg["pass"])
    total = len(P.list()[1])
    new = []
    start = max(1, total - cfg.get("scan_last", 5) + 1)
    for i in range(start, total + 1):
        try:
            raw = b"\n".join(P.retr(i)[1])
            msg = email.message_from_bytes(raw)
            mid = msg.get("Message-ID", f"idx-{i}")
            if mid in seen:
                continue
            mark_seen(seen, mid)
            sender = dh(msg.get("From"))
            subj = dh(msg.get("Subject"))
            body = get_body(msg)
            new.append({"id": mid, "title": f"来自 {sender}，主题：{subj}", "body": body})
        except Exception as e:
            print(f"[mail] 第 {i} 封处理失败: {e}", flush=True)
    P.quit()
    return new
