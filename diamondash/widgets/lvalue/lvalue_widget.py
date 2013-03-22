import json
from pkg_resources import resource_string

from twisted.python import log
from twisted.web.template import XMLString

from diamondash import utils, ConfigError
from diamondash.widgets import Widget
from diamondash.backends.graphite import GraphiteBackend


class LValueWidget(Widget):

    __DEFAULTS = {'time_range': '1d'}
    __CONFIG_TAG = 'diamondash.widgets.lvalue.LValueWidget'

    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    MODEL = 'LValueWidgetModel'
    VIEW = 'LValueWidgetView'

    loader = XMLString(resource_string(__name__, 'template.xml'))

    def __init__(self, backend, time_range, **kwargs):
        super(LValueWidget, self).__init__(**kwargs)
        self.backend = backend
        self.time_range = time_range

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(LValueWidget, cls).parse_config(config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        if 'target' not in config:
            raise ConfigError("All LValueWidgets need a target")

        config['time_range'] = utils.parse_interval(config['time_range'])

        # We have this set to use the Graphite backend for now, but the
        # type of backend could be made configurable in future
        config['backend'] = GraphiteBackend.from_config({
            'bucket_size': config['time_range'],
            'metrics': [{
                'target': config.pop('target'),
                'null_filter': 'zeroize',
            }]
        }, class_defaults)

        return config

    def format_data(self, prev, last):
        prev_y, last_y = prev['y'], last['y']
        diff_y = last_y - prev_y
        percentage = diff_y / (prev_y or 1)

        from_time = last['x']
        to_time = from_time + self.time_range - 1

        return json.dumps({
            'lvalue': last_y,
            'from': from_time,
            'to': to_time,
            'diff': diff_y,
            'percentage': percentage,
        })

    def handle_backend_response(self, metric_data):
        if not metric_data:
            log.msg("LValueWidget '%s' received empty response from backend")
            return self.format_data({'x': 0, 'y': 0}, {'x': 0, 'y': 0})

        datapoints = metric_data[0]['datapoints'][-2:]
        if len(datapoints) < 2:
            length = len(datapoints)
            log.msg("LValueWidget '%s' received too few datapoints (%s < 2)"
                    % (self.title, length))
            return self.format_data(
                *([{'x': 0, 'y': 0} for i in range(2 - length)] + datapoints))

        return self.format_data(*datapoints)

    def handle_render_request(self, request):
        d = self.backend.get_data(from_time=self.time_range * -2)
        d.addCallback(self.handle_backend_response)
        return d
