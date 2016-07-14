import subprocess

def RunError(object):
    def __init__(self, command, returncode, stdout, stderr):
        self.cmd = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "Command '{}' returned exit status {} with STDOUT:\n{}\nSTDERR:\n{}".format(
            self.cmd, self.returncode, self.stdout, self.stderr)

def run_command(command, input=''):
    if isinstance(command, str):
        import shlex
        cmd_str = command
        command = shlex.split(command)
    else:
        command = map(str, command)
        import pipes
        cmd_str = ' '.join(map(pipes.quote, command))
    print 'Running ' + cmd_str
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    out, err = proc.communicate(input=input)
    if proc.returncode != 0:
        raise RunError(cmd_str, proc.returncode, out, err)
    return out


