#!/data/data/com.termux/files/usr/bin/bash
# -*- coding: utf-8 -*-
# 🐳🔔 鲸铃 · 一键安装脚本（Termux 版）
# 用法：把本文件和整个开源版文件夹一起放进手机，进目录后敲  bash install.sh
# 它会自动：查/装 Python → 建目录 → 检查代码 → 提示你填 config → 起服务

set +e
echo ""
echo "🐳🔔 鲸铃 · 一键安装"
echo "----------------------------------------"

# ---------- 0. 定位自己所在目录 ----------
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="$HOME/jingling"
echo "[1/5] 安装目录：$HOME_DIR"

# ---------- 1. 检查 Python ----------
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "[2/5] 没找到 Python，尝试自动安装……"
    if command -v pkg >/dev/null 2>&1; then
        pkg update -y >/dev/null 2>&1
        pkg install -y python >/dev/null 2>&1
    fi
    if command -v python >/dev/null 2>&1; then PY=python
    elif command -v python3 >/dev/null 2>&1; then PY=python3
    else
        echo "❌ 装 Python 失败。请手动敲：pkg update -y && pkg install -y python"
        exit 1
    fi
fi
echo "[2/5] Python 就绪：$($PY --version 2>&1)"

# ---------- 2. 检查 requests ----------
$PY -c "import requests" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "      补装 requests……"
    $PY -m pip install -q requests >/dev/null 2>&1
    $PY -c "import requests" >/dev/null 2>&1 || echo "      ⚠️ requests 没装上，跑起来若报错再手动：pip install requests"
fi
echo "[3/5] 依赖检查完毕"

# ---------- 3. 拷贝代码到 ~/jingling ----------
mkdir -p "$HOME_DIR"
cp -rf "$SRC_DIR"/* "$HOME_DIR"/ 2>/dev/null
cd "$HOME_DIR"
echo "[4/5] 代码已放到 $HOME_DIR"

# ---------- 4. 提示填配置 ----------
echo ""
echo "----------------------------------------"
echo "⚠️ 还差一步：填 config.json"
echo "----------------------------------------"
echo "用任意文本编辑器打开：$HOME_DIR/config.json"
echo "把里面 3 处占位符换成你自己的："
echo "  1) provider.use 那段里的邮箱/授权码（如果你用邮箱源）"
echo "  2) engine.api_key —— 你的 AI 密钥（如 DeepSeek）"
echo "  3) waker.url —— 你的接收端地址（默认 http://127.0.0.1:8901/wake）"
echo ""
echo "改完回车，我帮你起服务；不想改也直接回车（会用一个测试配置起来）。"
read -p "改好了吗？按回车继续…… " _junk

# ---------- 5. 起服务 ----------
echo ""
echo "[5/5] 正在启动……"
pkill -f "core.py" 2>/dev/null
pkill -f "sleeper.py" 2>/dev/null
sleep 1

# 起通用出口
nohup $PY sleeper.py > sleeper.log 2>&1 &
sleep 1
# 起门铃
nohup $PY core.py > frame.log 2>&1 &
sleep 2

echo ""
echo "----------------------------------------"
echo "✅ 起好了！"
echo "----------------------------------------"
echo "看门铃在干嘛："
echo "  cat $HOME_DIR/frame.log      # 门铃日志"
echo "  cat $HOME_DIR/sleeper.log    # 出口日志"
echo "  cat $HOME_DIR/data/inbox.txt # 收到的消息"
echo ""
echo "浏览器打开（同机）："
PORT=$(grep -o '"port"[^,]*' config.json | grep -o '[0-9]\+' | head -1)
echo "  http://127.0.0.1:${PORT:-8899}"
echo ""
echo "想停止：pkill -f core.py; pkill -f sleeper.py"
echo "（可选）想开机自启/常驻：bash $HOME_DIR/watchdog.sh &"
echo ""
echo "🐳 有问题就把 frame.log 内容发出来问。"
