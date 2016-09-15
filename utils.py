import subprocess
import common

def RunError(Exception):
    def __init__(self, command, returncode, stdout, stderr):
        self.cmd = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "Command '{}' returned exit status {} with STDOUT:\n{}\nSTDERR:\n{}".format(
            self.cmd, self.returncode, self.stdout, self.stderr)

def run_command(command, input=None, returncodes=[0], **kwargs):
    if isinstance(command, str):
        cmd_str = '"{}"'.format(command)
    else:
        command = map(str, command)
        # import pipes
        # cmd_str = ' '.join(map(pipes.quote, command))
        cmd_str = str(command)
    common.log_debug('Running ' + cmd_str)
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.PIPE, **kwargs)
    out, err = proc.communicate(input=input)

    if returncodes:
        if proc.returncode != 0:
            raise RunError(cmd_str, proc.returncode, out, err)
        return out
    return proc.returncode


