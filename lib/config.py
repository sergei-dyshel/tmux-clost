import os.path
import os
import __main__

from . import environment, log

context_configs = []
global_options = None

def read():
    import yaml
    user_file = environment.get_var('config_file')
    global context_configs
    user_cfg = {}
    if user_file and os.path.isfile(user_file):
        with open(user_file) as f:
            user_cfg = yaml.load(f)
        context_configs = user_cfg.get('contexts', [])

    default_file = os.path.join(environment.get_var('main_dir'), 'config.yml')
    with open(default_file) as f:
        default_cfg = yaml.load(f)

    global global_options
    global_options = CombinedOptions(
        DictOptions(user_cfg.get('options')),
        DictOptions(default_cfg['options']))


class BaseOptions(object):
    def get_option(self, opt_name, cmd_name=None):
        raise NotImplementedError


class DictOptions(BaseOptions):
    def __init__(self, dict_):
        self._dict = dict_
    def get_option(self, opt_name, cmd_name=None):
        if not self._dict:
            return None
        try:
            return self._dict[cmd_name][opt_name]
        except KeyError:
            try:
                return self._dict[opt_name]
            except KeyError:
                return None


class CombinedOptions(BaseOptions):
    def __init__(self, *options_list):
        self._options_list = options_list
    def get_option(self, opt_name, cmd_name=None):
        for options in self._options_list:
            res = options.get_option(opt_name, cmd_name)
            if res is not None:
                return res
        return None





def get_contexts():
    global user_cfg
    return user_cfg['contexts']

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




