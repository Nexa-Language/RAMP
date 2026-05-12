#!/bin/bash
set -e

# 环境变量
export OPENAI_API_BASE="https://aihub.arcsysu.cn/v1"
export OPENAI_API_KEY="sk-Yq-qWVwmUvF8EpJdM-We2Q"
export OPENAI_MODEL_NAME="minimax-m2.5"

# 第二批模型列表
MODELS=(
  "minimax-m2.5"
  "qwen-omni-turbo"
  "qwen3-coder-flash"
  "qwen3.5-plus-2026-02-15"
  "qwen3.6-plus"
)

# 并行启动评测
for model in "${MODELS[@]}"; do
  echo "启动评测: $model"
  bash eval/run_openhands_eval.sh "$model" &
  sleep 2
done

echo "第二批评测已全部启动"
wait
echo "第二批评测完成"