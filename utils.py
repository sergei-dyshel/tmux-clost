def run_command(command, input=''):
    import subprocess
    if isinstance(command, str):
        import shlex
        command = shlex.split(command)
    else:
        command = map(str, command)
    import pipes
    print 'Running ' + ' '.join(map(pipes.quote, map(str, command)))
    proc = subprocess.Popen(command,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    out, _ = proc.communicate(input=input)
    return out


