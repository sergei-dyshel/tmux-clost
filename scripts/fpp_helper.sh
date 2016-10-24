#!/bin/bash -
pane=$1
shift
tmux send-keys -l -t $pane ' ' "$*"

