#!/data/data/com.termux/files/usr/bin/bash
# 🐳🔔 鲸铃一键启动（Termux里跑这个）
# 用法：bash ~/jingling/start.sh

cd "$(dirname "$0")"

# 先清旧的
pkill -f core.py 2>/dev/null
pkill -f sleeper.py 2>/dev/null
sleep 1

# 清"已见"记忆（想重扫就留着这行，不想重扫就注释掉）
# rm -f data/seen.json

# 起 sleeper（被唤醒的AI接收端）
if [ -f sleeper.py ]; then
  nohup python3 sleeper.py >> sleeper.log 2>&1 &
  sleep 2
fi

# 起 core（门铃主程序）
nohup python3 core.py >> jingling.log 2>&1 &
sleep 2

# 起看门狗（保活）
nohup bash watchdog.sh >> watchdog.log 2>&1 &

echo "🐳🔔 鲸铃已启动：门铃 + sleeper + 看门狗"
echo "查看：tail -f ~/jingling/jingling.log"
