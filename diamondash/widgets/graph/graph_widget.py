import json

from diamondash import utils, ConfigError
from diamondash.widgets import Widget
from diamondash.backends.graphite import GraphiteBackend


class GraphWidget(Widget):

    __DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
    }
    __CONFIG_TAG = 'diamondash.widgets.graph.GraphWidget'

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    MODEL = 'GraphWidgetModel'
    VIEW = 'GraphWidgetView'

    def __init__(self, **kwargs):
        super(GraphWidget, self).__init__(**kwargs)
        self.backend = kwargs['backend']

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(GraphWidget, cls).parse_config(config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.setdefaults(config, cls.__DEFAULTS, defaults)

        metric_configs = config.get('metrics')
        if metric_configs is None:
            raise ConfigError(
                'Graph Widget "%s" needs metrics.' % config['name'])

        metric_defaults = config.get('metric_defaults', {})
        metric_defaults['bucket_size'] = config['bucket_size']
        metric_configs = [cls.parse_metric_config(m, metric_defaults)
                          for m in metric_configs]

        # We have this set to use the Graphite backend for now, but the type of
        # backend could be made configurable in future
        config['backend'] = GraphiteBackend.from_config({
            'from_time': config['time_range'],
            'metrics': metric_configs
        }, class_defaults)

        config['client_config']['model']['metrics'] = [
            m['metadata']['client_config'] for m in metric_configs]

        return config

    @classmethod
    def parse_metric_config(cls, config, metric_defaults={}):
        """
        Parses a metric config given in a graph config into a config useable by
        the backend.
        """
        config = utils.setdefaults(config, metric_defaults)

        name = config.get('name')
        if name is None:
            raise ConfigError('Every graph metric needs a name.')

        title = config.get('title', name)
        name = utils.slugify(name)
        client_config = {'name': name, 'title': title}

        config['metadata'] = {
            'name': name,
            'title': title,
            'client_config': client_config
        }

        return config

    def process_backend_response(self, metric_data):
        x_values = [d['x'] for m in metric_data for d in m['datapoints']] + [0]
        y_values = [d['y'] for m in metric_data for d in m['datapoints']] + [0]
        domain = (min(x_values), max(x_values))
        range = (min(y_values), max(y_values))

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
        d = self.backend.get_data()
        d.addCallback(self.process_backend_response)
        return d
