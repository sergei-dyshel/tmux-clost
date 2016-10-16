#!/usr/bin/env python

import sys
import traceback
import argparse
import os.path
import os

import common
import log
import tmux
import setup
import history
import output
import commands


def handle_cmd(cmd):
    try:
        cmd()
    except BaseException as exc:
        if sys.stdin.isatty():
            # executed manually by user
            raise
        else:
            # executed by tmux

            log.error(traceback.format_exc())
            msg = 'Clost: failed with {}: {}'.format(exc.__class__.__name__,
                                                     exc)
            ERROR_TIMEOUT = 5000
            tmux.display_message(msg, ERROR_TIMEOUT)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('command', choices=commands.list_names())

    args = parser.parse_args()
    log.info('Called with {}', sys.argv[1:])

    handle_cmd(commands.get(args.command))

if __name__ == '__main__':
    main()
