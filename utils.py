import subprocess
import common
import collections

import log

RunResult = collections.namedtuple('RunResult',
                                   ['returncode', 'stdout', 'stderr'])

class RunError(Exception):
    def __init__(self, command, result):
        self.cmd = command
        self.result = result
        log.error(
            "Command '{}' exited exit status {} with STDOUT:\n{}\nSTDERR:\n{}",
            command, result.returncode, self._shorten(result.stdout), self._shorten(result.stderr))

    # TODO: use shorten from copy_output (with cutting middle)
    def _shorten(self, out):
        return out if len(out) < 1024 else "(long output)"

    def __str__(self):
        return "Command '{}' returned {}".format(self.cmd,
                                                 self.result.returncode)


def run_command(command, input=None, returncodes=[0], **kwargs):
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


    if returncodes and proc.returncode not in returncodes:
        raise RunError(cmd_str, result)
    return result


