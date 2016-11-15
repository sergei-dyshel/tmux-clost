from . import utils

def copy_xsel(text=None, file=None):
    cmd = 'xsel --input --clipboard'
    if file is not None:
        cmd = 'cat {} | {}'.format(file, cmd)
    return utils.run_command(cmd, shell=True, input=text).stdout

def copy_xclip(text=None, file=None):
    cmd = 'xclip -selection clipboard {}'.format(file or '')
    #  http://stackoverflow.com/questions/19101735/keyboard-shortcuts-in-tmux-deactivated-after-using-xclip/21190234#21190234
    return utils.run_command(cmd, shell=True, pipe=False, input=text)

def copy(out):
    # fixes problems with improper characters (such as line endings)
    # out = unicode(out, encoding='utf8', errors='ignore')
    copy_xclip(text=out)

def copy_file(path):
    copy_xclip(file=path)

