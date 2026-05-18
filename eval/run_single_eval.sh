#!/bin/bash
# 单个模型评测脚本
# 用法: ./run_single_eval.sh <model_name>
set -e

MODEL="$1"
if [ -z "$MODEL" ]; then
  echo "Usage: $0 <model_name>"
  exit 1
fi

PROJ_DIR="/root/proj/Paper/EXPERIMENT/RAMP"
YATCC_DIR="$PROJ_DIR/data/YatCC"
LOG_DIR="$PROJ_DIR/eval/logs"
RESULT_DIR="$PROJ_DIR/eval/results/openhands"
VENV="$PROJ_DIR/.venv-openhands"

mkdir -p "$LOG_DIR" "$RESULT_DIR"

echo "=== 启动评测: $MODEL ==="
echo "  时间: $(date)"
echo "  日志: $LOG_DIR/openhands-${MODEL}.log"

cd "$PROJ_DIR"

# 运行 OpenHands 评测
. "$VENV/bin/activate"
export OPENHANDS_SUPPRESS_BANNER=1
export OPENAI_API_BASE="https://aihub.arcsysu.cn/v1"
export OPENAI_API_KEY="sk-Yq-qWVwmUvF8EpJdM-We2Q"
export OPENAI_MODEL_NAME="$MODEL"

python src/run_openhands.py \
  --model "$MODEL" \
  --tasks 0-5 \
  --max-iterations 100 \
  --workspace "$YATCC_DIR" \
  2>&1 | tee "$LOG_DIR/openhands-${MODEL}.log"

echo "=== 评测完成: $MODEL ==="
echo "  时间: $(date)"

# 收集结果
python eval/collect_and_update.py 2>&1 | tail -5
