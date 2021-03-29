import os

import yaml


class ConfigParser:
    def __init__(self):
        os.environ["__cfg4py_server_role__"] = "TEST"

    def parse_config(self, module_name):
        cfg = None
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml'), 'r') as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)
        return cfg[module_name]