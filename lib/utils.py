import subprocess
import re
import pipes
import os
import time
import shlex

from . import log

def shlex_join(args):
    return ' '.join(pipes.quote(str(a)) for a in args)


def shorten(s, max_len, balance=0.5, separator='...'):
    if len(s) <= max_len:
        return s
    total = max_len - len(separator)
    left = int(total * balance)
    right = total - left
    return s[0:left] + separator + s[-right:]

def dashes(s):
    return s.replace('_', '-')


def count_lines(s):
    return s.count('\n') + 1


def single_to_list(x):
    return x if isinstance(x, list) else [] if x is None else [x]


class RunResult(object):
    def __init__(self, stdout='', stderr='', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __str__(self):
        return 'RunResult(returncode={}, stdout={}, stderr={})'.format(
                self.returncode, repr(shorten(self.stdout, 40)),
                repr(shorten(self.stderr, 40)))


class RunError(Exception):
    def __init__(self, cmd, result):
        self.cmd = cmd
        self.result = result

    def __str__(self):
        return "Command '{}' exited with {}".format(self.cmd, self.result)


DEV_NULL = open('/dev/null', 'rb+')

def run_command(command,
                input=None,
                returncodes=[0],
                pipe=True,
                ignore_err=None,
                env=None,
                **kwargs):
    if isinstance(command, str):
        cmd_str = '"{}"'.format(command)
    else:
        command = map(str, command)
        cmd_str = shlex_join(command)
    log.debug('Running ' + cmd_str)

    if env:
        new_env = os.environ.copy()
        new_env.update(env)
    else:
        new_env = None
    proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE if pipe else DEV_NULL,
            stdin=subprocess.PIPE if input else DEV_NULL,
            stderr=subprocess.PIPE if pipe else DEV_NULL,
            env=new_env,
            **kwargs)

    if pipe or input:
        stdout, stderr = proc.communicate(input=input)
    else:
        stdout = stderr = None
        proc.wait()
    result = RunResult(
        returncode=proc.returncode, stdout=stdout, stderr=stderr)


    if (returncodes and proc.returncode not in returncodes and
        (ignore_err is None or re.match(ignore_err, stderr) is None)):
        raise RunError(cmd_str, result)
    return result


def unquote(s):
    for q in ['"', "'"]:
        if s[0] == q and s[-1] == q:
            return s[1:-1]

