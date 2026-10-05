# 🐳🔔 鲸铃 · 使用说明书

> 一个**脱离任何 App 的独立门铃**：定时查你的信箱/平台，有新消息就叫醒你的 AI，并弹到你眼前。
> 纯 Python 标准库，不要装额外依赖（除了 requests）。

---

## 一、它是干啥的（30秒看懂）

```
① 轮询：每 N 秒查一次你的信箱，有没有新信
② AI：把新信喂给一个 AI，让它用一句话说清"谁来信、说了啥、要不要紧"
③ 唤醒：把这个消息"叫醒"给你的 AI / 推到网页上 / 发通知
④ 网页：你打开浏览器，能看到门铃响了几次、每次收啥、AI 回啥
```

**全程不依赖任何 App，跑在你自己的手机/电脑/服务器上。**

---

## 二、三块积木（想改哪儿改哪儿）

鲸铃是**可插拔**的，由三块"积木"拼成，全部在 `config.json` 里选：

| 积木 | 干啥 | 现成有啥 | 换法 |
|---|---|---|---|
| **provider** 数据源 | 去哪个平台找新消息 | `mail`（邮箱POP3） | 改 `provider.use`，或照着 `template.py` 写新的 |
| **engine** AI引擎 | 用哪个 AI 理解消息 | `deepseek` | 改 `engine.use`，或写新的 |
| **waker** 唤醒器 | 怎么把消息叫醒/推出 | `http`（POST到一个地址） | 改 `waker.use`，或写新的 |

---

## 三、三步跑起来

### 第①步：装 Python（Termux里）
```bash
pkg update -y && pkg install -y python && pip install requests
```
> 如果 `pkg update` 卡住报 `Network is unreachable`，先换源：
> ```bash
> sed -i 's@^\(deb.*stable main\)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main@' $PREFIX/etc/apt/sources.list && pkg update -y
> ```

### 第②步：改 config.json（填你自己的）
```json
{
  "interval": 60,
  "port": 8899,
  "provider": {
    "use": "mail",
    "pop_host": "pop.126.com",
    "pop_port": 995,
    "user": "你的邮箱@126.com",
    "pass": "你的授权码",
    "limit": 5
  },
  "engine": {
    "use": "deepseek",
    "api_base": "https://api.deepseek.com/chat/completions",
    "api_key": "sk-你的key",
    "model": "deepseek-chat",
    "system_prompt": "你是信箱助理。用一句话说清：谁来信、说了啥、要不要紧。"
  },
  "waker": {
    "use": "http",
    "enabled": true,
    "wake_url": "http://127.0.0.1:8911/wake"
  }
}
```

### 第③步：起服务（Termux里）
```bash
cd ~/jingling
pkill -f core.py; pkill -f sleeper.py; sleep 1
nohup python3 core.py > jingling.log 2>&1 &
# 想看网页：
am start -a android.intent.action.VIEW -d "http://127.0.0.1:8899"
```

---

## 四、想"被人叫醒"？配一个接收端

`waker` 会把消息 POST 到一个地址。你那边起一个能收 POST 的服务就行。

**最简版**（照抄 `sleeper.py`）：一个 HTTP 服务，收到 POST 就把内容打印/存下来/转发。

### 通用出口 sleeper.py 的三落点
| 落点 | 说明 |
|---|---|
| `data/woken.jsonl` | 原始日志（每行一条 JSON） |
| `data/inbox.txt` | 给人看的收件箱（`[时间] 标题`） |
| 环境变量 `JINGLING_WEBHOOK` | 有值时，把消息**转发**过去（微信/Server酱/你自己的AI接口） |

### 接你自己的 AI —— 改一个函数就行
打开 `sleeper.py`，找到：
```python
def handle(msg):
    # === 你的AI入口 ===
    # 把这里换成你的逻辑：调你的模型API、发微信、推通知...
    ...
    return "ok"
```
**这，就是"叫醒你的AI"的全部工作。**

### 配 webhook 转发（例子）
```bash
export JINGLING_WEBHOOK="https://你的通知服务/webhook"
bash start.sh
```
门铃一响，消息就自动转发到那儿。

---

## 五、想接新平台/新模型？（照着 template 写）

每个文件夹里都有 `template.py`，照着抄：

- **接新数据源** → `providers/你的名字.py`，需要 `NAME` + `poll(cfg, seen)`
- **接新AI** → `engines/你的名字.py`，需要 `NAME` + `think(msg, cfg)`
- **接新唤醒方式** → `wakers/你的名字.py`，需要 `NAME` + `wake(payload, cfg)`

写完，在 `config.json` 里把 `use` 改成你的名字就生效了。

---

## 六、文件清单

```
jingling/
├─ core.py              主程序（不用改）
├─ config.json          配置（改这里）
├─ index.html           网页
├─ sleeper.py           示例：被唤醒的"AI接收端"
├─ providers/mail.py    ① 邮箱数据源
├─ providers/template.py
├─ engines/deepseek.py  ② DeepSeek引擎
├─ engines/template.py
├─ wakers/http.py       ③ HTTP唤醒器
└─ wakers/template.py
```

---

## 八、常驻保活（别被清后台）

### 一键启动
Termux 里跑：
```bash
bash ~/jingling/start.sh
```
它会：清旧进程 → 起 sleeper → 起 core → 起看门狗 → 报"已启动"。

### 看门狗（掉了自动拉起）
`watchdog.sh` 每 60 秒检查一次，`core.py`/`sleeper.py` 掉了就重新起。
```bash
nohup bash ~/jingling/watchdog.sh >> ~/jingling/watchdog.log 2>&1 &
```

### 防杀（Termux 别被系统清理）
1. **Termux 里申请唤醒锁**：`termux-wake-lock`
2. **手机设置**：给 Termux **关闭电池优化 / 允许后台运行**（设置→应用→Termux→省电策略→无限制）
3. **开机自启**（可选）：装 Termux:Boot 应用，在 `~/.termux/boot/` 放个脚本调 `start.sh`

### 一个坑
Termux 里脚本第一行要用：
```
#!/data/data/com.termux/files/usr/bin/bash
```
（不是 `/bin/bash`，Termux 路径不一样）

---

## 七、踩过的坑（省你时间）

- ❌ Termux 默认源在境外连不上 → **换清华源**
- ❌ `pkg install python-requests` 找不到包 → 用 **`pip install requests`**
- ❌ 端口报 `Address already in use` → **换端口**（沙盒/Termux 共用网络会撞）
- ❌ 门铃重启后不响 → **删 `data/seen.json`** 清"已见"记忆重扫
- ❌ AI 把朋友信判成垃圾邮件 → **prompt 里明确说清"来的是谁"**
- ❌ waker 报 `'url'` 键错 → config 键名要跟积木里读的一致（`wake_url`）
- ❌ **默认 config 是接 Galatea 花园的**（provider=galatea_sse）→ 第一次用**必须先换成你自己的数据源**（如 mail），否则拿不到消息
- ❌ **sleeper 的端口在 `sleeper.py` 顶上的 `JINGLING_SLEEPER_PORT` 环境变量里**（默认 8911）→ config 里 `waker.wake_url` 的端口必须跟它一致，不然叫不醒
- ❌ **engine 只读 title 会漏正文** → `deepseek.py` 已同时喂 title+body，自己写 engine 时注意 body 要用上

---

*—— 鲸铃 v0.4.2 · 2026-10-05 · shadow*
