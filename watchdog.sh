#!/data/data/com.termux/files/usr/bin/bash
# 🐳🔔 鲸铃看门狗：每60秒检查一次，掉了就拉起
# 用法：nohup bash ~/jingling/watchdog.sh > ~/jingling/watchdog.log 2>&1 &

cd "$(dirname "$0")"   # 切到鲸铃目录

while true; do
  TS=$(date '+%Y-%m-%d %H:%M:%S')

  # 检查 core.py
  if ! pgrep -f "core.py" > /dev/null; then
    echo "[$TS] core.py 掉了，拉起..."
    nohup python3 core.py >> jingling.log 2>&1 &
  fi

  # 检查 sleeper.py（如果用它被唤醒）
  if [ -f sleeper.py ] && ! pgrep -f "sleeper.py" > /dev/null; then
    echo "[$TS] sleeper.py 掉了，拉起..."
    nohup python3 sleeper.py >> sleeper.log 2>&1 &
  fi

  sleep 60
done
