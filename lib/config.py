import os
import os.path


from .environment import env
from . import log


context_configs = []
global_options = None


class Config(object):
    options = {}
    contexts = []

    def _add_context(self, context, is_user):
        ctx_names = [ctx['name'] for ctx in self.contexts]
        if context['name'] in ctx_names:
            if is_user:
                log.warning('Context {} repeats in user config', context['name'])
            return
        context['options'] = context.get('options', {})
        self.contexts.append(context)

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

        for ctx in user_cfg.get('contexts', []):
            self._add_context(ctx, is_user=True)
        for ctx in default_cfg['contexts']:
            self._add_context(ctx, is_user=False)


config = Config()
