#!/usr/bin/env python

import tmux
import common
import history
import utils
import setup

def main():
    config = common.get_config()
    max_prompt_lines = max(len(context['patterns'])
                           for context in config['contexts'].itervalues())
    lines = tmux.capture_pane(max_lines=max_prompt_lines,
                              till_cursor=True,
                              splitlines=True)
    ctx_name, ctx_conf = common.find_context(lines, config)
    if ctx_name is None:
        raise Exception('Matching context not found')

    all_history = history.load_history(ctx_name)
    setup.unbind_enter()
    line = utils.run_command(
        ['fzf-tmux', '-d', '20%', '--no-sort'],
        input=all_history)
    setup.bind_enter()
    line = line.strip()
    if line:
        tmux.insert_text(line)

if __name__ == '__main__':
    common.wrap_main(main)
