import os.path
import re
import inspect
import sys

from . import (alias, tmux, log, history, config, common, utils, output,
               environment, clipboard, context)

def single_to_list(x):
    return x if isinstance(x, list) else [] if x is None else [x]

class Command(object):
    requires_context = True
    silent_no_context = False
    args = []

    def init(self, ctx=None):
        self.ctx = ctx

    def run(self):
        raise NotImplementedError

    def get_option(self, opt_name):
        return self.ctx.options.get_option(opt_name, self.name)

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    def add_subparser(cls, subparsers):
        subparser = subparsers.add_parser(cls.name().replace('_', '-'))
        subparser.set_defaults(cmd_class=cls)
        for arg_name, arg_type, arg_help in cls.args:
            name_dashes = arg_name.replace('_', '-')
            if arg_type == bool:
                subparser.add_argument('--' + name_dashes, dest=arg_name,
                    action='store_true', help=arg_help)
                no_help = 'Do not ' + arg_help[0].lower() + arg_help[1:]
                subparser.add_argument('--no-' + name_dashes, dest=arg_name,
                    action='store_false', help=no_help)
            else:
                subparser.add_argument('--' + name_dashes,
                    dest=arg_name, type=arg_type, help=arg_help)

    def strip_suggestion(self):
        escape_code_list = single_to_list(
            self.get_option('suggestion_color_escape_code'))
        if not escape_code_list:
            return
        _, splits = context.capture_escaped_line()
        while splits:
            last = splits[-1]
            if not last or context.is_escape_code(last):
                del splits[-1]
                continue
            break
        log.info(splits)
        if len(splits) <= 1 or splits[-2] not in escape_code_list:
            return
        suggestion = splits[-1]
        log.debug('Suggestion: {}', suggestion)

        if self.ctx.cmd_line.endswith(suggestion):
            self.ctx.cmd_line = self.ctx.cmd_line[0:-len(suggestion)]
            log.debug('Stripped suggestion')


class press_enter(Command):
    silent_no_context = True
    args = [
        ('auto_expand_aliases', bool, 'Automatically expand aliases')
    ]

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
        line = utils.select_split_pipe(cmd)
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
        out = output.get(self.ctx.pattern, self.get_option('max_lines'))
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
        snippets_dir = environment.get_var('snippets_dir')
        ctx_snippets_dir = os.path.join(snippets_dir, self.ctx.name)
        if not os.path.isdir(ctx_snippets_dir):
            return
        snippet_names = os.listdir(ctx_snippets_dir)

        snippet_name = utils.select_split(snippet_names)
        if not snippet_name:
            return

        with open(os.path.join(ctx_snippets_dir, snippet_name), 'rb+') as f:
            tmux.insert_text(
                f.read()[:-1], bracketed=self.get_option('bracketed_paste'))

class edit_cmd(Command):
    def run(self):
        cmd_file = environment.temp_file('cmd.txt')
        with open(cmd_file, 'w') as f:
            f.write(self.ctx.cmd_line)
        # editor = common.get_config()['editor']
        # editor = environment.expand_path(config.get_option('editor'))
        editor = self.get_option('editor')
        res = utils.run_in_split_window('{} {}'.format(editor, cmd_file))
        if res != 0:
            log.info(
                'Editing command line was cancelled (editor exited with status {})',
                res)
            return
        with open(cmd_file) as f:
            tmux.replace_cmd_line(
                f.read().strip(), bracketed=self.get_option('bracketed_paste'))


class show_context(Command):
    def run(self):
        print '''tmux-clost current context:
        CONTEXT: {self.ctx.name}
        PATTERN: {self.ctx.pattern}
        CMD: {self.ctx.cmd_line}
        '''.format(**locals())

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


def get_all():
    return [x for x in globals().itervalues()
            if inspect.isclass(x) and issubclass(x, Command) and x != Command]
