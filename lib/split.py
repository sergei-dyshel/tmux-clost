import time
import os
import contextlib

from .environment import env
from .utils import RunResult
from . import tmux, log, utils
from .config import config

def wait(pred, delay=1, timeout=10):
    elapsed = 0
    while elapsed <= timeout:
        if pred():
            return
        time.sleep(delay)
        elapsed += delay
    raise Exception('Timeout')


def capture_output_split(shell_cmd):
    out_file = env.temp_file_path('split.out')
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
    return RunResult(
        stdout=stdout, stderr='', returncode=returncode)

@contextlib.contextmanager
def _temp_fifo(name):
    path = env.temp_file_path(name)
    if os.path.exists(path):
        os.unlink(path)
    os.mkfifo(path)
    yield path
    os.unlink(path)

def bind_cmd(key, cmd, **kwargs):
    tmux.set_option('@clost', env.exec_path, global_=True)
    return tmux.bind_key(key, ['run-shell', '-b', '#{@clost} ' + cmd], **kwargs)

def bind_enter():
    bind_cmd('Enter', 'press-enter', table='root')


@contextlib.contextmanager
def temporarily_unbind_enter():
    if not config.options['intercept_enter']:
        yield
    else:
        tmux.unbind_key('Enter', no_prefix=True)
        yield
        bind_enter()


def run_in_split_window(shell_cmd, capture_output=False):
    CHANNEL = 'clost'

    with _temp_fifo('split.output') as output_fifo, \
            _temp_fifo('split.returncode') as return_fifo, \
            temporarily_unbind_enter():
        if capture_output:
            shell_cmd += ' > ' + output_fifo
        # trap "tmux wait-for -S {CHANNEL}" 0
        split_cmd = '''
        {shell_cmd}
        echo $? > {return_fifo}
        '''.format(**locals())
        tmux.run(['split-window', split_cmd])
        if capture_output:
            log.debug('Waiting for output')
            with open(output_fifo) as f:
                stdout = f.read().strip()
            log.debug('Command written {} lines: {}',
                      utils.count_lines(stdout), repr(
                              utils.shorten(stdout, 80)))
        log.debug('Waiting for return code')
        with open(return_fifo) as f:
            returncode = int(f.read())
        log.debug('Command returned with code {}', returncode)
        # tmux.run(['wait-for', CHANNEL])

        if capture_output:
            return RunResult(
                stdout=stdout, stderr='', returncode=returncode)
        else:
            return returncode


def select_split_pipe(cmd, selector):
    res = run_in_split_window(
            '{} | {}'.format(cmd, selector), capture_output=True)
    if res.returncode == 0:
        return res.stdout
    elif res.returncode == 130:
        return ''
    else:
        log.error('selector {} returned {} with stdout:\n{}\nstderr:\n{}'.format(
                selector, res.returncode, res.stdout, res.stderr))
        raise Exception('selector {} returned unexpected output'.format(selector))

def select_split(lines, selector):
    lines_file = env.temp_file_path('selector.lines')
    with open(lines_file, 'w') as f:
        f.write('\n'.join(map(str.strip, lines)))
    return select_split_pipe('cat {}'.format(lines_file), selector)

