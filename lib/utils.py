import subprocess
import collections
import re

import tmux
import common
import log
import setup

RunResult = collections.namedtuple('RunResult',
                                   ['returncode', 'stdout', 'stderr'])

class RunError(Exception):
    def __init__(self, command, result):
        self.cmd = command
        self.result = result
        log.error(
            "Command '{}' exited with status {} with STDOUT:\n{}\nSTDERR:\n{}",
            command, result.returncode, self._shorten(result.stdout), self._shorten(result.stderr))

    # TODO: use shorten from copy_output (with cutting middle)
    def _shorten(self, out):
        return out if len(out) < 1024 else "(long output)"

    def __str__(self):
        return "Command '{}' returned {}".format(self.cmd,
                                                 self.result.returncode)


def run_command(command,
                input=None,
                returncodes=[0],
                ignore_err=None,
                **kwargs):
    if isinstance(command, str):
        cmd_str = '"{}"'.format(command)
    else:
        command = map(str, command)
        # import pipes
        # cmd_str = ' '.join(map(pipes.quote, command))
        cmd_str = str(command)
    log.debug('Running ' + cmd_str)
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.PIPE, **kwargs)

    stdout, stderr = proc.communicate(input=input)
    result = RunResult(returncode=proc.returncode, stdout=stdout, stderr=stderr)


    if (returncodes and proc.returncode not in returncodes and
        (ignore_err is None or re.match(ignore_err, stderr) is None)):
        raise RunError(cmd_str, result)
    return result


def capture_output_split(shell_cmd):
    out_file = common.get_temp_file('split.out')
    full_cmd = '{shell_cmd} >{out_file}'.format(**locals())
    returncode = run_in_split_window(full_cmd)
    with open(out_file) as outf:
        return RunResult(
            stdout=outf.read().strip(), stderr='', returncode=returncode)

def run_in_split_window(shell_cmd):
    CHANNEL = 'clost'
    returncode_file = common.get_temp_file('split.returncode')
    split_cmd = '''
    trap "tmux wait-for -S {CHANNEL}" 0
    {shell_cmd}
    echo $? > {returncode_file}
    '''.format(**locals())

    tmux._run(['split-window', split_cmd])
    tmux._run(['wait-for', CHANNEL])
    with open(returncode_file) as retf:
        return int(retf.read())

def select_split(lines):
    lines_file = common.get_temp_file('selector.lines')
    with open(lines_file, 'w') as f:
        f.write('\n'.join(map(str.strip, lines)))
    try:
        setup.unbind_enter()
        res = capture_output_split('cat {} | fzf --no-sort'.format(lines_file))
    finally:
        setup.bind_enter()
    if res.returncode == 0:
        return res.stdout
    elif res.returncode == 130:
        return ''
    else:
        log.error('fzf returned unexpected output: \n' + res.stdout)
        raise Exception('fzf returned unexpected output')


