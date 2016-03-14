#!/bin/bash

plug_dir=$(dirname $0)
$plug_dir/setup.py > $plug_dir/setup_log.txt 2>&1
