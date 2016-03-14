#!/usr/bin/env python

import tmux
import common
import os.path
import sys
import os

def script_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), name))

def bind_key(function):
    workdir = common.get_workdir()
    key = common.get_config_var(function + '_key')
    if key is not None:
        tmux.tmux_bind_key(
            key, ['run-shell',
                  '{} >{}/last.log 2>&1'.format(
                      script_path(function + '.py'), workdir)])


def main():
    bind_key('copy_output')

    # config_file = common.get_config_var('config_file', mandatory=True)

if __name__ == '__main__':
    common.wrap_main(main)

