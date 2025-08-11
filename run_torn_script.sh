#!/bin/bash
set -e

SCRIPT_NAME="$1"
VENV_BIN_DIR="$HOME/jpr_env/bin"
TORN_SCRIPTS_DIR="$HOME/torn_scripts"
TORN_DATA_DIR="$HOME/torn_data"
LOG_DIR="$TORN_DATA_DIR/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/${SCRIPT_NAME%.py}_$(date +'%Y-%m-%d_%H-%M').log"

source "$VENV_BIN_DIR/activate"
python "$TORN_SCRIPTS_DIR/$SCRIPT_NAME" >> "$LOG_FILE" 2>&1

if [ ! -s "$LOG_FILE" ]; then
  rm "$LOG_FILE"
fi
