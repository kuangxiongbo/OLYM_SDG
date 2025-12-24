#!/bin/bash
# 启动新的模块化应用

cd "$(dirname "$0")"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=development

# 启动应用
python app.py



