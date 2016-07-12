#!/usr/bin/env python

import setup
import subprocess
import sys

def fzf_tmux_fix(argv):
    setup.unbind_enter()
    proc = subprocess.Popen(argv[1:], shell=True)
    proc.wait()
    setup.bind_enter()
    return proc.returncode

if __name__ == '__main__':
    sys.exit(fzf_tmux_fix(sys.argv))

