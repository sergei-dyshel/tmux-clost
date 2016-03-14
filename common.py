import tmux

ERROR_TIMEOUT = 5000

def wrap_main(main):
    try:
        main()
    except BaseException as exc:
        import sys
        if sys.stdin.isatty():
            # executed by user
            raise
        else:
            # executed by tmux
            import traceback
            traceback.print_exc(file=sys.stdout)
            import inspect
            import os.path
            script = os.path.basename(inspect.getsourcefile(main))
            msg = 'Clost: {} failed with {}: {}'.format(
                script, exc.__class__.__name__, exc)
            tmux.display_message(msg, ERROR_TIMEOUT)

def get_config_var(opt_name, default=None, mandatory=False):
    full_opt_name = '@clost_' + opt_name
    value = tmux.get_option(full_opt_name)
    if 'unknown option' in value:
        if mandatory:
            raise Exception('Configuration option {} not defined or empty'.format(
                full_opt_name))
        else:
            return default
    return value

def get_config():
    config_file = get_config_var('config_file', mandatory=True)
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.load(f)
    return config

def get_workdir():
    workdir = get_config_var('workdir', mandatory=True)
    import os.path
    import os
    if not os.path.isdir(workdir):
        os.makedirs(workdir)
    return workdir
