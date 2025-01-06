#!/bin/bash

# Check and install required dependencies if not already installed
if ! command -v tmux &> /dev/null; then
    echo "tmux is not installed. Installing tmux..."
    sudo apt-get update
    sudo apt-get install -y tmux
fi

if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Installing npm..."
    sudo apt-get update
    sudo apt-get install -y npm
fi

if ! command -v http-server &> /dev/null; then
    echo "http-server is not installed. Installing http-server..."
    sudo npm install -g http-server
fi

# Function to kill processes using specific ports
kill_port() {
    port=$1
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process using port $port (PID: $pid)"
        kill -9 $pid
    fi
}

# Kill processes using ports 8000 and 3000
kill_port 8000
kill_port 3000

# Stop and remove existing containers
docker compose down

# Kill any existing tmux sessions
tmux kill-server 2>/dev/null || true

# Build and start containers in detached mode
docker compose up -d

# Create a new tmux session
tmux new-session -d -s AudioGenEditor

# Split the window twice to create three panes
tmux split-window -h
tmux split-window -h

# Attach shells to containers and start the frontend server
tmux send-keys -t 0 "docker exec -it audiogeneditor-api-1 /bin/bash" C-m
tmux send-keys -t 1 "docker exec -it audiogeneditor-style-transfer-1 /bin/bash" C-m
tmux send-keys -t 2 "cd frontend && npx http-server --cors -p 3000" C-m

# Wait for shells to attach
sleep 2

# Download model from Hugging Face in the API container if it doesn't exist
tmux send-keys -t 0 "if [ ! -d \"model/stabilityai/stable-audio-open-1.0\" ]; then" C-m
tmux send-keys -t 0 "    huggingface-cli login --token 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" C-m
tmux send-keys -t 0 "    HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download stabilityai/stable-audio-open-1.0 --local-dir model/stabilityai/stable-audio-open-1.0" C-m
tmux send-keys -t 0 "fi" C-m

# Then execute the Python processes
tmux send-keys -t 0 "python3 api.py" C-m
tmux send-keys -t 1 "python3 service.py" C-m

# Attach to the tmux session
tmux attach-session -t AudioGenEditor