import yaml


class Yaml_Model:

    def read(self, file):
        with open(file, encoding='utf-8') as yaml_file:
            data = yaml.safe_load(yaml_file)
            if data is not None:
                return data
            else:
                return None

    def read_node(self, file, node):
        with open(file, encoding='utf-8') as yaml_file:
            data = yaml.safe_load(yaml_file)
            if data is not None:
                return data[node]
            else:
                return None
