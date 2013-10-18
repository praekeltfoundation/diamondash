from uuid import uuid4

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.dynamic import DynamicWidgetConfig, DynamicWidget


class GraphWidgetConfig(DynamicWidgetConfig):
    DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
        'align_to_start': False,
        'dotted': False,
        'smooth': False,
    }

    TYPE_NAME = 'graph'

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    @classmethod
    def parse(cls, config):
        super(GraphWidgetConfig, cls).parse(config)

        if 'metrics' not in config:
            raise ConfigError(
                "Graph Widget '%s' needs metrics." % config['name'])

        config['time_range'] = utils.parse_interval(config['time_range'])
        bucket_size = utils.parse_interval(config.pop('bucket_size'))

        config['backend'].update({
            'bucket_size': bucket_size,
            'metrics': [cls.parse_metric(m) for m in config.pop('metrics')],
        })

        if 'null_filter' in config:
            config['backend']['null_filter'] = config.pop('null_filter')

        backend_config_cls = cls.for_type(config['backend']['type'])
        config['backend'] = backend_config_cls.from_dict(config['backend'])

        config['client_config']['model'].update({
            'step': bucket_size,
            'metrics': [
                m['metadata']['client_config']
                for m in config['backend']['metrics']]
        })
        config['client_config']['view'].update({
            'dotted': config.pop('dotted'),
            'smooth': config.pop('smooth'),
        })

        return config

    @classmethod
    def parse_metric(cls, config):
        """
        Parses a metric config given in a graph config into a config useable by
        the backend.
        """
        if 'name' not in config:
            raise ConfigError('Every graph metric needs a name.')

        id = str(uuid4())
        name = config.pop('name')
        title = config.pop('title', name)
        name = utils.slugify(name)

        client_config = {
            'id': id,
            'name': name,
            'title': title
        }

        config['metadata'] = {
            'id': id,
            'name': name,
            'title': title,
            'client_config': client_config
        }

        return config


class GraphWidget(DynamicWidget):
    CONFIG_CLS = GraphWidgetConfig

    def process_backend_response(self, metric_data):
        for metric in metric_data:
            # x values are converted to milliseconds for client
            metric['datapoints'] = [{
                'x': d['x'],
                'y': d['y']
            } for d in metric['datapoints']]

        x_vals = [d['x'] for m in metric_data for d in m['datapoints']] or [0]
        y_vals = [d['y'] for m in metric_data for d in m['datapoints']] or [0]
        domain = (min(x_vals), max(x_vals))

        y_min = self.config['y_min'] if 'y_min' in self.config else min(y_vals)
        range = (y_min, max(y_vals))

        output_metric_data = [{
            'id': m['metadata']['id'],
            'datapoints': m['datapoints'],
        } for m in metric_data]

        return {
            'domain': domain,
            'range': range,
            'metrics': output_metric_data,
        }

    def get_snapshot(self):
        time_range = self.config['time_range']
        if self.config['align_to_start']:
            from_time = utils.floor_time(utils.now(), time_range)
        else:
            from_time = utils.relative_to_now(-time_range)

        d = self.backend.get_data(from_time=from_time)
        d.addCallback(self.process_backend_response)
        d.addErrback(self.handle_bad_backend_response)
        return d
