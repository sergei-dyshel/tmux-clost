from lib.tmux import run
for i in xrange(100):
    run(['display-message', '-p', '#{pane_id}'], cm=False)
    # run(['send-keys', 'Escape'], cm=False)
    # run(['list-keys'], cm=False)
