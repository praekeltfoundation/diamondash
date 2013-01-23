import json
from pkg_resources import resource_string

from twisted.web.template import XMLString

from diamondash import utils
from diamondash.exceptions import ConfigError
from diamondash.widgets.graphite import (
    MultiMetricGraphiteWidget, GraphiteWidgetMetric)


class GraphWidget(MultiMetricGraphiteWidget):
    loader = XMLString(resource_string(__name__, 'template.xml'))

    DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
    }

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    STYLESHEETS = ('graph/style.css',)
    JAVASCRIPTS = ('graph/graph-widget',)

    MODEL = ('graph/graph-widget', 'GraphWidgetModel')
    VIEW = ('graph/graph-widget', 'GraphWidgetView')

    @classmethod
    def parse_config(cls, config, defaults={}):
        config = super(GraphWidget, cls).parse_config(config, defaults)

        config = dict(cls.DEFAULTS, **config)
        utils.set_key_defaults(
            'diamondash.widgets.graph.GraphWidget', config, defaults)

        config['from_time'] = utils.parse_interval(config['time_range'])
        bucket_size = utils.parse_interval(config['bucket_size'])
        config['bucket_size'] = bucket_size

        m_configs = config.get('metrics', None)
        if m_configs is None:
            raise ConfigError(
                'Graph Widget "%s" needs metrics.' % config['name'])

        metrics = []
        m_defaults = config.get('metric_defaults', {})
        m_client_configs = []
        for m_config in m_configs:
            m_config['bucket_size'] = bucket_size
            metric = GraphWidgetMetric.from_config(m_config, m_defaults)
            m_client_configs.append(metric.client_config)
            metrics.append(metric)

        config['metrics'] = metrics
        config['client_config']['model']['metrics'] = m_client_configs

        return config

    def handle_graphite_render_response(self, data):
        metric_data = super(
            GraphWidget, self).handle_graphite_render_response(data)

        metric_output_data = [
            {'name': metric.name, 'datapoints': metric_datum['datapoints']}
            for metric, metric_datum in zip(self.metrics, metric_data)]

        return json.dumps(metric_output_data)


class GraphWidgetMetric(GraphiteWidgetMetric):
    """A metric displayed by a GraphiteWidget"""

    DEFAULTS = {'null_filter': 'skip'}

    def __init__(self, **kwargs):
        super(GraphWidgetMetric, self).__init__(**kwargs)
        self.name = kwargs['name']
        self.title = kwargs['title']
        self.client_config = kwargs['client_config']

    @classmethod
    def parse_config(self, config, defaults={}):
        config = super(GraphWidgetMetric, self).parse_config(config, defaults)

        name = config.get('name', None)
        if name is None:
            raise ConfigError('Every graph metric needs a name.')
        title = config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name
        config['client_config'] = {'name': name, 'title': title}

        return config

    def process_datapoints(self, datapoints):
        datapoints = super(
            GraphWidgetMetric, self).process_datapoints(datapoints)

        return [{'x': x, 'y': y} for y, x in datapoints]
