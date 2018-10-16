import os
import os.path
import collections


from .environment import env
from . import log


context_configs = []
global_options = None


class Config(object):
    options = {}
    contexts = []
    commands = collections.defaultdict(dict)
    contexts_by_name = {}

    def _add_context(self, context, is_user):
        if context['name'] in self.contexts_by_name:
            if is_user:
                log.warning('Context {} repeats in user config', context['name'])
            return
        context['options'] = context.get('options', {})
        context['commands'] = context.get('commands', {})
        self.contexts.append(context)
        self.contexts_by_name[context['name']] = context

    def read(self):
        import yaml
        user_file = env.vars['config_file']
        user_cfg = {}
        if user_file:
            if os.path.isfile(user_file):
                with open(user_file) as f:
                    user_cfg = yaml.load(f)
            else:
                log.warning('User config file {} does not exists, skipping',
                            user_file)

        default_file = os.path.join(env.src_dir, 'config.yml')
        with open(default_file) as f:
            default_cfg = yaml.load(f)

        self.options = default_cfg.get('options', {})
        self.options.update(user_cfg.get('options', {}))
        for cfg in [default_cfg, user_cfg]:
            for cmd_name, cmd_opts in cfg.get('commands', {}).iteritems():
                self.commands[cmd_name].update(cmd_opts)

        for ctx in user_cfg.get('contexts', []):
            self._add_context(ctx, is_user=True)
        for ctx in default_cfg['contexts']:
            self._add_context(ctx, is_user=False)


config = Config()
