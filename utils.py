import subprocess
import collections
import re

import log
import tmux
import common

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


def run_command(command, input=None, returncodes=[0], ignore_err=None, **kwargs):
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


def run_in_split_window(shell_cmd):
    CHANNEL = 'clost-split-done'
    out_file = common.get_temp_file('split.out')
    err_file = common.get_temp_file('split.err')
    returncode_file = common.get_temp_file
    split_cmd = '''
    trap "tmux wait-for -S {}" 0
    {}
    echo $? > /tmp/tmux-clost-edit-status.txt
    '''

    tmux._run(['split-window', split_cmd, ';', 'wait-for', 'clost-split-done'])
    # tmux.send_keys(['C-e', 'C-u'])
    # tmux.send_keys([exp], literally=True)




