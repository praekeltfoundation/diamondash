import json
from pkg_resources import resource_string

from twisted.web.template import XMLString

from diamondash import utils
from diamondash.exceptions import ConfigError
from diamondash.widgets.graphite import (
    SingleMetricGraphiteWidget, GraphiteWidgetMetric)


class LValueWidget(SingleMetricGraphiteWidget):
    loader = XMLString(resource_string(__name__, 'template.xml'))

    DEFAULTS = {
        'time_range': '1d',
        'metric_defaults': {'null_filter': 'noop'}
    }

    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    STYLESHEETS = ('lvalue/style.css',)
    JAVASCRIPTS = ('lvalue/lvalue-widget',)

    MODEL = ('lvalue/lvalue-widget', 'LValueWidgetModel')
    VIEW = ('lvalue/lvalue-widget', 'LValueWidgetView')

    def __init__(self, **kwargs):
        super(LValueWidget, self).__init__(**kwargs)
        self.time_range = kwargs['time_range']

    @classmethod
    def parse_config(cls, config, defaults={}):
        config = super(LValueWidget, cls).parse_config(config, defaults)

        config = utils.setdefaults(config, cls.DEFAULTS)
        config = utils.set_key_defaults(
            'diamondash.widgets.lvalue.LValueWidget', config, defaults)

        target = config.get('target', None)
        if target is None:
            raise ConfigError(
                "LValue widget %s needs a metric target" % config['name'])

        # Set the bucket size to the passed in time range (for eg, if 1d was
        # the time range, the data for the entire day would be aggregated).
        time_range = utils.parse_interval(config['time_range'])
        config['time_range'] = time_range
        config['bucket_size'] = time_range

        # Set the from param to double the bucket size. As a result, graphite
        # will return two datapoints for each metric: the previous value and
        # the last value. The last and previous values will be used to
        # calculate the percentage increase.
        config['from_time'] = int(time_range) * 2

        metric_defaults = config.get('metric_defaults', {})
        config['metric'] = GraphiteWidgetMetric.from_config(
            {'target': target, 'bucket_size': time_range}, metric_defaults)

        return config

    def handle_graphite_render_response(self, data):
        """
        Accepts graphite render response data and performs the data processing
        and formatting necessary to have the data useable by lvalue widgets on
        the client side.
        """
        datapoints = (
            super(LValueWidget, self).handle_graphite_render_response(data))

        prev, last = datapoints[-2:]

        prev_y, last_y = prev[0] or 0, last[0] or 0
        diff_y = last_y - prev_y

        percentage = (diff_y / prev_y) if prev_y != 0 else 0

        from_time = last[1] or 0
        to_time = from_time + self.time_range - 1

        return json.dumps({
            'lvalue': last_y,
            'from': from_time,
            'to': to_time,
            'diff': diff_y,
            'percentage': percentage,
        })
