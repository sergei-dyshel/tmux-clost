from . import config

import re

# source: http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
def camel_case_to_underscores(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class Command(object):
    needs_context = True
    needs_config = True
    args = []

    def init(self, context=None, command=None, output=None, pattern=None):
        self.context = context
        self.command = command
        self.output = output
        self.pattern = pattern

    def run(self):
        raise NotImplementedError

    def get_option(self, name, type=str):
        pass

    @classmethod
    def name(cls):
        return camel_case_to_underscores(cls.__name__)

    @classmethod
    def add_subparser(cls, subparsers):
        subparser = subparsers.add_subparser(cls.name())
        subparser.set_defaults(cmd_class=cls)
        for name, type, help in cls.args:
            name_dashes = name.replace('_', '-')
            if type == bool:
                subparser.add_argument('--' + name_dashes, dest=name, help=help)


