from pkg_resources import resource_string

from twisted.web.template import XMLString

from diamondash import utils, ConfigError
from diamondash.widgets.dynamic import DynamicWidget
from diamondash.backends import BadBackendResponseError
from diamondash.backends.graphite import GraphiteBackend


class LValueWidget(DynamicWidget):

    __DEFAULTS = {'time_range': '1d'}
    __CONFIG_TAG = 'diamondash.widgets.lvalue.LValueWidget'

    TYPE_NAME = 'lvalue'
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
        return {
            'value': last['y'],
            'from': last['x'],
            'to': last['x'] + utils.to_client_interval(self.time_range) - 1,
            'diff': diff_y,
            'percentage': diff_y / (prev['y'] or 1),
        }

    def handle_backend_response(self, metric_data, from_time):
        if not metric_data:
            raise BadBackendResponseError(
                "LValueWidget '%s' received empty response from backend")

        # convert from_time into the time unit used by the client side
        from_time = utils.to_client_interval(from_time)
        datapoints = metric_data[0]['datapoints']
        for datapoint in reversed(datapoints):
            if datapoint['x'] <= from_time:
                break
            datapoints.pop()
        datapoints = datapoints[-2:]

        if len(datapoints) < 2:
            length = len(datapoints)
            raise BadBackendResponseError(
                "LValueWidget '%s' received too few datapoints (%s < 2)"
                % (self.title, length))

        return self.format_data(*datapoints)

    def get_snapshot(self):
        # We ask the backend for data since 2 intervals ago so we can obtain
        # the previous value and calculate the increase/decrease since the
        # previous interval
        d = self.backend.get_data(from_time=self.time_range * -2)

        d.addCallback(self.handle_backend_response, utils.now())
        d.addErrback(self.handle_bad_backend_response)
        return d
