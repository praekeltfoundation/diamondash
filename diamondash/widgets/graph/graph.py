from uuid import uuid4

from diamondash import utils, ConfigError
from diamondash.widgets.dynamic import DynamicWidget
from diamondash.backends.graphite import GraphiteBackend


class GraphWidget(DynamicWidget):
    __DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
        'align_to_start': False,
        'dotted': False,
        'smooth': False,
    }
    __CONFIG_TAG = 'diamondash.widgets.graph.GraphWidget'

    TYPE_NAME = 'graph'
    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    def __init__(self, align_to_start=False, y_min=None, **kwargs):
        super(GraphWidget, self).__init__(**kwargs)
        self.align_to_start = align_to_start
        self.y_min = y_min

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(GraphWidget, cls).parse_config(config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        if 'metrics' not in config:
            raise ConfigError('Graph Widget "%s" needs metrics.'
                              % config['name'])

        metric_defaults = config.pop('metric_defaults', {})
        metric_configs = [cls.parse_metric_config(m, metric_defaults)
                          for m in config.pop('metrics')]

        config['time_range'] = utils.parse_interval(config['time_range'])
        bucket_size = utils.parse_interval(config.pop('bucket_size'))

        backend_config = {
            'bucket_size': bucket_size,
            'metrics': metric_configs
        }

        if 'null_filter' in config:
            backend_config['null_filter'] = config.pop('null_filter')

        # We have this set to use the Graphite backend for now, but the type of
        # backend could be made configurable in future
        config['backend'] = GraphiteBackend.from_config(
            backend_config, class_defaults)

        client_config = config['client_config']
        client_config['model'].update({
            'step': bucket_size * 1000,
            'metrics': [m['metadata']['client_config'] for m in metric_configs]
        })
        client_config['view'].update({
            'dotted': config.pop('dotted'),
            'smooth': config.pop('smooth'),
        })

        return config

    @classmethod
    def parse_metric_config(cls, config, metric_defaults={}):
        """
        Parses a metric config given in a graph config into a config useable by
        the backend.
        """
        config = utils.update_dict(config, metric_defaults)

        name = config.pop('name')
        if name is None:
            raise ConfigError('Every graph metric needs a name.')

        id = str(uuid4())
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

    def process_backend_response(self, metric_data):
        for metric in metric_data:
            # x values are converted to milliseconds for client
            metric['datapoints'] = [{
                'x': utils.to_client_interval(d['x']),
                'y': d['y']
            } for d in metric['datapoints']]

        x_vals = [d['x'] for m in metric_data for d in m['datapoints']] or [0]
        y_vals = [d['y'] for m in metric_data for d in m['datapoints']] or [0]
        domain = (min(x_vals), max(x_vals))

        y_min = self.y_min if self.y_min is not None else min(y_vals)
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
        if self.align_to_start:
            from_time = utils.floor_time(utils.now(), self.time_range)
        else:
            from_time = utils.relative_to_now(-self.time_range)

        d = self.backend.get_data(from_time=from_time)
        d.addCallback(self.process_backend_response)
        d.addErrback(self.handle_bad_backend_response)
        return d
