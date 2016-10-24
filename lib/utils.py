import subprocess
import re
import pipes
from argparse import Namespace

import tmux
import common
import log
import setup

def shlex_join(args):
    return ' '.join(pipes.quote(str(a)) for a in args)

class RunError(Exception):
    def __init__(self, command, result):
        self.cmd = command
        self.result = result
        log.error(
            "Command '{}' exited with status {} with STDOUT:\n{}\nSTDERR:\n{}",
            command, result.returncode, self._shorten(result.stdout), self._shorten(result.stderr))

    # TODO: use shorten from copy_output (with cutting middle)
    def _shorten(self, out):
        return out if not out or len(out) < 1024 else "(long output)"

    def __str__(self):
        return "Command '{}' returned {}".format(self.cmd,
                                                 self.result.returncode)

DEV_NULL = open('/dev/null', 'rb+')

def run_command(command,
                input=None,
                returncodes=[0],
                pipe=True,
                ignore_err=None,
                **kwargs):
    if isinstance(command, str):
        cmd_str = '"{}"'.format(command)
    else:
        command = map(str, command)
        cmd_str = str(command)
    log.debug('Running ' + cmd_str)
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE if pipe else DEV_NULL,
                     stdin=subprocess.PIPE if input else DEV_NULL,
                     stderr=subprocess.PIPE if pipe else DEV_NULL, **kwargs)

    if pipe or input:
        stdout, stderr = proc.communicate(input=input)
    else:
        stdout = stderr = None
        proc.wait()
    result = Namespace(
        returncode=proc.returncode, stdout=stdout, stderr=stderr)


    if (returncodes and proc.returncode not in returncodes and
        (ignore_err is None or re.match(ignore_err, stderr) is None)):
        raise RunError(cmd_str, result)
    return result


def capture_output_split(shell_cmd):
    out_file = common.get_temp_file('split.out')
    full_cmd = '{shell_cmd} >{out_file}'.format(**locals())
    returncode = run_in_split_window(full_cmd)
    with open(out_file) as outf:
        return Namespace(
            stdout=outf.read().strip(), stderr='', returncode=returncode)

def run_in_split_window(shell_cmd):
    CHANNEL = 'clost'
    returncode_file = common.get_temp_file('split.returncode')
    split_cmd = '''
    trap "tmux wait-for -S {CHANNEL}" 0
    {shell_cmd}
    echo $? > {returncode_file}
    '''.format(**locals())

    try:
        setup.unbind_enter()
        tmux.run(['split-window', split_cmd])
        tmux.run(['wait-for', CHANNEL])
    finally:
        setup.bind_enter()

    with open(returncode_file) as retf:
        return int(retf.read())

def select_split_pipe(cmd):
    res = capture_output_split('{} | fzf --no-sort --tac'.format(cmd))
    if res.returncode == 0:
        return res.stdout
    elif res.returncode == 130:
        return ''
    else:
        log.error('fzf returned unexpected output: \n' + res.stdout)
        raise Exception('fzf returned unexpected output')

def select_split(lines):
    lines_file = common.get_temp_file('selector.lines')
    with open(lines_file, 'w') as f:
        f.write('\n'.join(map(str.strip, lines)))
    return select_split_pipe('cat {}'.format(lines_file))

