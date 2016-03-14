#!/usr/bin/env python

import history, tmux, common

def main():
    config = common.get_config()
    max_prompt_lines = max(len(context['patterns'])
                           for context in config['contexts'].itervalues())
    lines = tmux.capture_pane(max_lines=max_prompt_lines,
                              till_cursor=True,
                              splitlines=True)
    ctx_name, ctx_conf = common.find_context(lines, config)
    if ctx_name is None:
        return
    patterns = ctx_conf['patterns']
    cmd = common.get_prompt_input(config, patterns[-1])
    if cmd:
        history.save_to_history(ctx_name, cmd)

if __name__ == '__main__':
    common.wrap_main(main)
