import json
from pkg_resources import resource_string

from twisted.web.template import XMLString

from diamondash import utils, ConfigError
from diamondash.widgets.dynamic import DynamicWidget
from diamondash.backends import BadBackendResponseError
from diamondash.backends.graphite import GraphiteBackend


class LValueWidget(DynamicWidget):

    __DEFAULTS = {'time_range': '1d'}
    __CONFIG_TAG = 'diamondash.widgets.lvalue.LValueWidget'

    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    MODEL = 'LValueWidgetModel'
    VIEW = 'LValueWidgetView'

    loader = XMLString(resource_string(__name__, 'template.xml'))

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
            'time_aligner': 'floor',
            'metrics': [{
                'target': config.pop('target'),
                'null_filter': 'skip',
            }]
        }, class_defaults)

        return config

    def format_data(self, prev, last):
        diff_y = last['y'] - prev['y']

        # 'to' gets added the widget's time range converted from its internal
        # representation (in seconds) to the representation used by the client
        # side. The received datapoints are already converted by the backend,
        # so each widget type (lvalue, graph, etc) does not have to worry about
        # converting the datapoints.
        return json.dumps({
            'lvalue': last['y'],
            'from': utils.to_client_interval(last['x']),
            'to': utils.to_client_interval(last['x'] + self.time_range - 1),
            'diff': diff_y,
            'percentage': diff_y / (prev['y'] or 1),
        })

    def handle_backend_response(self, metric_data, from_time):
        if not metric_data:
            raise BadBackendResponseError(
                "LValueWidget '%s' received empty response from backend")

        datapoints = metric_data[0]['datapoints']
        last = utils.pop_until(datapoints, lambda d: d['x'] <= from_time)
        prev = utils.pop_until(
            datapoints, lambda d: d['x'] <= from_time - self.time_range)

        if last is None or prev is None:
            raise BadBackendResponseError(
                "LValueWidget did not receive all the datapoints it needed "
                "the backend")

        return self.format_data(prev, last)

    def handle_render_request(self, request):
        # We ask the backend for data since the start of yesterday to calculate
        # the increase or decrease between today and yesterday
        now = utils.now()
        from_time = utils.floor_time(now - self.time_range, self.time_range)
        d = self.backend.get_data(from_time=from_time)

        d.addCallback(self.handle_backend_response, now)
        d.addErrback(self.handle_bad_backend_response)
        return d
