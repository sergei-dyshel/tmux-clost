import subprocess
import re
import pipes
from argparse import Namespace
import os
import time

import tmux
import common
import log

from . import environment

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


def unquote(s):
    for q in ['"', "'"]:
        if s[0] == q and s[-1] == q:
            return s[1:-1]

def wait(pred, delay=1, timeout=10):
    elapsed = 0
    while elapsed <= timeout:
        if pred():
            return
        time.sleep(delay)
        elapsed += delay
    raise Exception('Timeout')



def capture_output_split(shell_cmd):
    out_file = environment.temp_file('split.out')
    if os.path.isfile(out_file):
        os.remove(out_file)
    full_cmd = '{shell_cmd} >{out_file}'.format(**locals())
    returncode = run_in_split_window(full_cmd)

    def pred():
        try:
            statinfo = os.stat(out_file)
        except OSError:
            return False
        return statinfo.st_size != 0
    wait(pred, delay=0.1, timeout=5)
    with open(out_file) as outf:
        stdout = outf.read().strip()
    return Namespace(
        stdout=stdout, stderr='', returncode=returncode)

def run_in_split_window(shell_cmd):
    CHANNEL = 'clost'
    returncode_file = environment.temp_file('split.returncode')
    split_cmd = '''
    trap "tmux wait-for -S {CHANNEL}" 0
    {shell_cmd}
    echo $? > {returncode_file}
    '''.format(**locals())

    try:
        tmux.run(['split-window', split_cmd])
        tmux.run(['wait-for', CHANNEL])
    finally:
        pass

    with open(returncode_file) as retf:
        return int(retf.read())

def select_split_pipe(cmd):
    res = capture_output_split('{} | fzf --no-sort'.format(cmd))
    if res.returncode == 0:
        return res.stdout
    elif res.returncode == 130:
        return ''
    else:
        log.error('fzf returned unexpected output: \n' + res.stdout)
        raise Exception('fzf returned unexpected output')

def select_split(lines):
    lines_file = environment.temp_file('selector.lines')
    with open(lines_file, 'w') as f:
        f.write('\n'.join(map(str.strip, lines)))
    return select_split_pipe('cat {}'.format(lines_file))

