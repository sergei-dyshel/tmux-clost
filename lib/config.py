import os.path
import os
import __main__

from . import environment, log

def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, basestring):
        if value.lower() in ['on', 'true', 'yes', 'y']:
            return True
        elif value.lower() in ['off', 'false', 'no', 'n']:
            return False
        else:
            raise ValueError('Can not parse boolean "{}"'.format(value))

def parse_value(value, type):
    try:
        if type in [int, str]:
            if isinstance(value, bool):
                raise ValueError
            return type(value)
        elif type == bool:
            return parse_bool(value)
    except ValueError:
        raise Exception('Can not parse "{}" as {}'.format(value,
                                                          type.__name__))
    assert False

def get_nested_dict_value(nested_dict, path):
    if not isinstance(nested_dict, dict):
        return nested_dict
    try:
        return get_nested_dict_value(nested_dict[path[0]], path[1:])
    except (KeyError, IndexError):
        return None

user_cfg = {}
default_cfg = {}

def read():
    import yaml
    user_file = environment.var.config_file
    default_file = os.path.join(environment.var.main_dir, 'config.yml')
    if user_file and os.path.isfile(user_file):
        with open(user_file) as f:
            global user_cfg
            user_cfg = yaml.load(f)
    with open(default_file) as f:
        global default_cfg
        default_cfg = yaml.load(f)

def get_option(name, cmd=None):
    def get_cfg_option(cfg, name, cmd):
        res = None
        if cmd is not None:
            res = get_nested_dict_value(cfg, [cmd, name])
        if res is None:
            res = get_nested_dict_value(cfg, [name])
        return res

    res = get_cfg_option(user_cfg, name, cmd)
    if res is None:
        res = get_cfg_option(default_cfg, name, cmd)
    return res




