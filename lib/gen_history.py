import time
import datetime

_TIMESTAMP_FORMAT='%Y-%m-%d__%H:%M:%S'

def current_line(cmd):
    return time.strftime(_TIMESTAMP_FORMAT, time.localtime()) + ' ' + cmd

def parse_line(line, cmd_only=False):
    ts_str, cmd = line.split(' ', 1)
    cmd = cmd.strip()
    if cmd_only:
        return cmd
    ts = datetime.datetime.strptime(ts_str, _TIMESTAMP_FORMAT)
    return ts, cmd
