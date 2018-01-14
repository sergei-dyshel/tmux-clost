from lib.output import get_old, get_new

text = '''
[1234] command with output
this is output
[123] just command
[12] another command
'''

pattern = '\[\S+@.+\]\$'
with open('/home/sergei/tmux-history.log') as f:
    text = f.read()

# for i in xrange(1000):
#     get_old(pattern, text)

# import re
import re2 as re
import regex

def find_last(pattern, text):
    def last(iter):
        elem = None
        for elem in iter:
            pass
        return elem
    obj = re.compile(pattern)
    pos = len(text)
    CHUNK = 65 * 1024
    while True:
        if pos > CHUNK: pos = pos - CHUNK
        elif pos == 0: return None
        else: pos = 0
        m = last(obj.finditer(text, pos))
        if m: return m

# print find_last(pattern, text).group(0)
for i in xrange(1000):
    m = find_last(pattern, text)
    # m = regex.search(pattern, text, regex.REVERSE)

