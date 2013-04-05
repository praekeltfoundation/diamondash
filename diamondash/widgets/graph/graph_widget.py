import json

from diamondash import utils, ConfigError
from diamondash.widgets import Widget
from diamondash.backends.graphite import GraphiteBackend


class GraphWidget(Widget):
    __DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
        'dotted': False,
        'smooth': True,
    }
    __CONFIG_TAG = 'diamondash.widgets.graph.GraphWidget'

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    MODEL = 'GraphWidgetModel'
    VIEW = 'GraphWidgetView'

    def __init__(self, backend, time_range, **kwargs):
        super(GraphWidget, self).__init__(**kwargs)
        self.backend = backend
        self.time_range = time_range

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

        # We have this set to use the Graphite backend for now, but the type of
        # backend could be made configurable in future
        config['backend'] = GraphiteBackend.from_config({
            'bucket_size': bucket_size,
            'metrics': metric_configs
        }, class_defaults)

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

        title = config.pop('title', name)
        name = utils.slugify(name)
        client_config = {'name': name, 'title': title}

        config['metadata'] = {
            'name': name,
            'title': title,
            'client_config': client_config
        }

        return config

    def process_backend_response(self, metric_data):
        x_vals = [d['x'] for m in metric_data for d in m['datapoints']] or [0]
        y_vals = [d['y'] for m in metric_data for d in m['datapoints']] or [0]
        domain = (min(x_vals), max(x_vals))
        range = (min(y_vals), max(y_vals))

        output_metric_data = [{
            'name': m['metadata']['name'],
            'datapoints': m['datapoints']
        } for m in metric_data]

        return json.dumps({
            'domain': domain,
            'range': range,
            'metrics': output_metric_data,
        })

    def handle_render_request(self, request):
        d = self.backend.get_data(from_time=-self.time_range)
        d.addCallback(self.process_backend_response)
        return d
