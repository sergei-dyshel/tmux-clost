#!/usr/bin/env python

import history
import common
import tmux

def main(argv):
    config = common.get_config()
    ctx, _, cmd = common.get_context(config, silent=True)
    tmux.send_keys(['Enter'])
    if ctx is None:
        return

    common.log_info('Saving command "{}"', cmd)
    if cmd:
        history.save_to_history(ctx['name'], cmd)

if __name__ == '__main__':
    common.wrap_main(main)
