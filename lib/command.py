import os.path
import re
import inspect
import sys
import json

from .environment import env
from .config import config
from . import (alias, tmux, log, history, common, utils, output,
               clipboard, context, split)

def single_to_list(x):
    return x if isinstance(x, list) else [] if x is None else [x]

class Command(object):
    requires_context = True
    silent_no_context = False
    opt_arg_defs = []
    pos_arg_defs = []

    def init(self, ctx, args):
        self.ctx = ctx
        self.args = args

    def run(self):
        raise NotImplementedError

    def get_option(self, opt_name):
        try:
            return self.args[opt_name]
        except KeyError:
            try:
                return self.ctx.options[opt_name]
            except KeyError:
                return config.options[opt_name]

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    def add_subparser(cls, subparsers):
        subparser = subparsers.add_parser(utils.dashes(cls.name()))
        subparser.set_defaults(cmd_class=cls)
        for arg_name, arg_type, arg_help in cls.opt_arg_defs:
            name_dashes = utils.dashes(arg_name)
            if arg_type == bool:
                subparser.add_argument('--' + name_dashes, dest=arg_name,
                    action='store_true', help=arg_help)
                no_help = 'Do not ' + arg_help[0].lower() + arg_help[1:]
                subparser.add_argument('--no-' + name_dashes, dest=arg_name,
                    action='store_false', help=no_help)
            else:
                subparser.add_argument('--' + name_dashes,
                    dest=arg_name, type=arg_type, help=arg_help)
        for arg_name, arg_type, arg_help in cls.pos_arg_defs:
            name_dashes = utils.dashes(arg_name)
            subparser.add_argument(arg_name, type=arg_type, help=arg_help)

    def strip_suggestion(self):
        escape_code_list = single_to_list(
            self.get_option('suggestion_color_escape_code'))
        if not escape_code_list:
            return
        _, splits = context.capture_escaped_line()
        while splits:
            last = splits[-1]
            if context.is_escape_code(last):
                del splits[-1]
                continue
            break
        log.info('Splitted cmd with escape codes: {}', splits)
        if not splits:
            return

        suggestion = splits[-1]
        del splits[-1]

        has_suggestion_escape = False
        while splits:
            last = splits[-1]
            if not context.is_escape_code(last):
                break
            if last in escape_code_list:
                has_suggestion_escape = True
                break
            del splits[-1]

        if not has_suggestion_escape:
            return

        log.debug('Suggestion: {}', suggestion)

        if self.ctx.cmd_line.endswith(suggestion):
            self.ctx.cmd_line = self.ctx.cmd_line[0:-len(suggestion)]
        else:
            log.error('Error stripping suggestion')


class press_enter(Command):
    silent_no_context = True

    def run(self):
        if self.ctx is None or not self.ctx.cmd_line:
            tmux.send_keys(['Enter'])
            log.info('Skipping empty command line')
            return
        with common.handle_exceptions(lambda: tmux.send_keys(['Enter'])):
            cmd = self.ctx.cmd_line
            newcmd = alias.expand(cmd, self.ctx.cfg)
            if newcmd.strip() != cmd.strip():
                cmd = newcmd
                tmux.replace_cmd_line(
                    cmd, bracketed=self.get_option('bracketed_paste'))
        tmux.send_keys(['Enter'])
        with common.handle_exceptions():
            log.info('Saving command "{}"', cmd)
            history.save_to_history(self.ctx.name, cmd)

class expand_alias(Command):
    def run(self):
        cmd = self.ctx.cmd_line
        exp = alias.expand(cmd, self.ctx.cfg)
        if cmd != exp:
            tmux.replace_cmd_line(
                exp, bracketed=self.get_option('bracketed_paste'))
        else:
            raise common.ClostError('No alias found')



class escape_codes(Command):
    requires_context = False

    def run(self):
        line, splits = context.capture_escaped_line()
        print 'Full line:', repr(line)
        print 'Splitted:\n', '\n'.join(repr(s) for s in splits)


class search_history(Command):
    def run(self):
        cmd = 'cat {} | cut -d" " -f2- '.format(
                history.get_history_path(self.ctx.name))
        cmd_line = self.ctx.cmd_line
        if cmd_line:
            escaped = cmd_line.replace('"', r'\"')
            cmd = cmd + '| grep -F -- "{}"'.format(escaped)
        line = split.select_split_pipe(cmd)
        if line:
            tmux.replace_cmd_line(
                line, bracketed=self.get_option('bracketed_paste'))

class copy_output(Command):
    def run(self):
        out = output.get(self.ctx.pattern, self.get_option('max_lines'))

        output_file = environment.expand_path(self.get_option('output_file'))
        if output_file:
            log.info('Saving output to {}', output_file)
            with open(output_file, 'w') as f:
                f.write(out)
            clipboard.copy_file(output_file)
        else:
            clipboard.copy(out)

        num_lines = out.count('\n') + 1
        common.display_status('Captured {} lines (context: {})', num_lines,
                            self.ctx.name)

class last_output(Command):
    def run(self):
        out = self.ctx.get_output()
        sys.stdout.write(out)
        num_lines = out.count('\n') + 1
        common.display_status('Captured {} lines (context: {})', num_lines,
                            self.ctx.name)


class path_picker(Command):
    def run(self):
        out = output.get(self.ctx.pattern, self.get_option('max_lines'))
        save_path = environment.temp_file('output.txt')
        with open(save_path, 'w') as f:
            f.write(out)
        pane_id = tmux.get_variable('pane_id')
        helper = os.path.join(environment.get_var('main_dir'), 'scripts', 'fpp_helper.sh')
        res = utils.run_in_split_window('cat {} | /home/sergei/opt/fpp/fpp -nfc -ai -ni -c {}'.format(
            save_path, helper))
        if res == 0:
            tmux.run(['paste-buffer', '-p', '-b', 'clost_fpp'])

class insert_snippet(Command):
    def run(self):
        snippets_dir = env.vars['snippets_dir']
        ctx_snippets_dir = os.path.join(snippets_dir, self.ctx.name)
        if not os.path.isdir(ctx_snippets_dir):
            return
        snippet_names = os.listdir(ctx_snippets_dir)

        snippet_name = split.select_split(snippet_names)
        if not snippet_name:
            return

        with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
            tmux.insert_text(
                f.read()[:-1], bracketed=self.get_option('bracketed_paste'))

class edit_cmd(Command):
    def run(self):
        cmd_file = env.temp_file_path('cmd.txt')
        with open(cmd_file, 'w') as f:
            f.write(self.ctx.cmd_line)
        # editor = common.get_config()['editor']
        # editor = environment.expand_path(config.get_option('editor'))
        editor = self.get_option('editor')
        res = split.run_in_split_window(
                '{} {}'.format(editor, cmd_file), capture_output=False)
        if res != 0:
            log.info(
                'Editing command line was cancelled (editor exited with status {})',
                res)
            return
        with open(cmd_file) as f:
            new_cmd = f.read().strip()
            if new_cmd == self.ctx.cmd_line:
                log.info('Command line not changed during editing')
            else:
                tmux.replace_cmd_line(
                        new_cmd, bracketed=self.get_option('bracketed_paste'))


class show_context(Command):
    def run(self):
        sys.stdout.write('''tmux-clost current context:
CONTEXT: {self.ctx.name}
PATTERN: {self.ctx.pattern}
CMD: {self.ctx.cmd_line}
'''.format(**locals()))

class prev_prompt(Command):
    def run(self):
        tmux.run(['copy-mode'])
        hist_size = int(tmux.get_variable('history_size'))
        pos = int(tmux.get_variable('scroll_position')) + 1
        while pos < hist_size:
            new_pos = min(pos + 1000, hist_size)
            lines = tmux.capture_pane(start=-new_pos, end=-pos, dump=True)
            try:
                offset = list(context.finditer_prompts(
                    lines, self.ctx.pattern))[-1].start
            except IndexError:
                pos = new_pos + 1
                continue
            lineno = lines.count('\n', 0, offset)
            tmux.run(['send-keys', '-X', 'goto-line', new_pos - lineno])
            return
        raise common.ClostError('No previous prompt')

class next_prompt(Command):
    def run(self):
        tmux.run(['copy-mode'])
        scroll_pos = int(tmux.get_variable('scroll_position'))
        if scroll_pos == 0:
            raise common.ClostError('Already at bottom of history')
        pos = scroll_pos - 1
        lines = tmux.capture_pane(start=-pos, dump=True)
        try:
            offset = next(context.finditer_prompts(lines,
                                                  self.ctx.pattern)).start
        except StopIteration:
            raise common.ClostError('No next prompt')
        lineno = lines.count('\n', 0, offset)
        new_pos = max(pos - lineno, 0)
        tmux.run(['send-keys', '-X', 'goto-line', new_pos])

class cmd_line(Command):
    def run(self):
        if not tmux.pane_in_mode():
            res = self.ctx.cmd_line
        else:
            scroll_pos = int(tmux.get_variable('scroll_position'))
            lines = tmux.capture_lines(start=-scroll_pos)
            iter_ = context.finditer_prompts(lines, self.ctx.pattern)
            try:
                prompt = next(iter_)
                cl_end = lines.find('\n', prompt.end)
                res = lines[prompt.end:cl_end].lstrip()
            except StopIteration:
                raise common.ClostError('No command line found below')
        log.debug('Captured command line: {}', res)
        sys.stdout.write(res)



class sleep(Command):
    def run(self):
        import time
        time.sleep(10)


class wait_for_prompt(Command):
    requires_context = False
    pos_arg_defs = [('cmd', str, 'Command to run')]

    def run(self):
        tmux.set_option(
                'wait_for_prompt_pane',
                tmux.get_variable('pane_id'),
                clost=True,
                window=True)
        tmux.set_option(
                'wait_for_prompt_cmd',
                self.args['cmd'],
                clost=True,
                window=True)
        tmux.set_option('monitor-silence',
                        config.options['wait_for_prompt_monitor_interval'])


class check_for_prompt(Command):
    requires_context = False
    pos_arg_defs = [('window_id', str,
                     'ID of window on which silence occured')]

    def _disable_waiting(self, target=None):
        tmux.set_option('monitor-silence', 0, window=True, target=target)
        tmux.set_option('wait_for_prompt_pane', None,
                clost=True, window=True, target=target)
        tmux.set_option('wait_for_prompt_cmd', None,
                clost=True, window=True, target=target)

    def run(self):
        win_id = self.args['window_id']
        pane_id = tmux.get_option(
                'wait_for_prompt_pane', clost=True, window=True)

        if not pane_id:
            log.warning('Not waiting for prompt in this window')
        elif pane_id not in tmux.list_panes(target=win_id):
            log.warning('The pane waiting for prompt no longer belongs to this window')
            self._disable_monitor(target=win_id)
        elif context.get_current(target=pane_id):
            log.info('Pane reached prompt')
            cmd = tmux.get_option(
                    'wait_for_prompt_cmd', clost=True, window=True)
            env = dict(
                    TMUX_WINDOW=tmux.get_variable('window_name', pane=pane_id))
            utils.run_command(cmd, shell=True, env=env, pipe=True)
        else:
            log.info('Prompt not detected, continuing waiting...')
            return

        self._disable_waiting(target=win_id)


class configure(Command):
    requires_context = False

    def _bind_cmd(self, key, cmd, **kwargs):
        tmux.set_option('@clost', env.exec_path, global_=True)
        return tmux.bind_key(key, ['run-shell', '-b', '#{@clost} ' + cmd], **kwargs)

    def run(self):
        if config.options['intercept_enter']:
            tmux.bind_key('Enter', ['send-keys', 'Enter'])
            self._bind_cmd('Enter', 'press-enter', table='root')

        if config.options['allow_wait_for_prompt']:
            tmux.set_option('silence-action', 'any', global_=True)
            tmux.set_hook('alert-silence',
                    'run-shell -b "#{@clost} check-for-prompt #{hook_window}"')


def get_all():
    return [x for x in globals().itervalues()
            if inspect.isclass(x) and issubclass(x, Command) and x != Command]
