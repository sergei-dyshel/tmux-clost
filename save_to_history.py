#!/usr/bin/env python

import history
import common
import tmux

import log

def main(argv):
    config = common.get_config()
    ctx, _, cmd = common.get_context(config, silent=True)
    tmux.send_keys(['Enter'])
    if ctx is None:
        return

    log.info('Saving command "{}"', cmd)
    if cmd:
        history.save_to_history(ctx['name'], cmd)

if __name__ == '__main__':
    common.wrap_main(main)
