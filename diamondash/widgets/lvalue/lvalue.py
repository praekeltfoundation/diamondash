from itertools import takewhile

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.dynamic import DynamicWidgetConfig, DynamicWidget
from diamondash.backends import BadBackendResponseError


class LValueWidgetConfig(DynamicWidgetConfig):
    TYPE_NAME = 'lvalue'

    DEFAULTS = {
        'time_range': '1d'
    }

    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    @classmethod
    def parse(cls, config):
        config = super(LValueWidgetConfig, cls).parse(config)

        if 'target' not in config:
            raise ConfigError("All LValueWidgets need a target")

        config['time_range'] = utils.parse_interval(config['time_range'])

        config['backend'].update({
            'bucket_size': config['time_range'],
            'time_aligner': 'floor',
            'metrics': [{
                'target': config.pop('target'),
                'null_filter': 'skip',
            }]
        })

        backend_config_cls = cls.for_type(config['backend']['type'])
        config['backend'] = backend_config_cls(config['backend'])

        return config


class LValueWidget(DynamicWidget):
    CONFIG_CLS = LValueWidgetConfig

    def format_data(self, prev, last):
        time_range = self.config['time_range']

        # 'to' gets added the widget's time range converted from its internal
        # representation (seconds) to the representation used by the client
        # side (milliseconds).
        return {
            'from': last['x'],
            'to': last['x'] + time_range - 1,
            'last': last['y'],
            'prev': prev['y'],
        }

    def handle_backend_response(self, metric_data, from_time):
        if not metric_data:
            raise BadBackendResponseError(
                "LValueWidget '%s' received empty response from backend")

        datapoints = metric_data[0]['datapoints']
        prev_time = from_time - self.config['time_range']

        prev = None
        for n in takewhile(lambda d: d['x'] <= prev_time, datapoints):
            prev = n

        last = None
        for n in takewhile(lambda d: d['x'] <= from_time, datapoints):
            last = n

        if last is None or prev is None:
            raise BadBackendResponseError(
                "LValueWidget did not receive all the datapoints it needed "
                "the backend")

        return self.format_data(prev, last)

    def get_snapshot(self):
        now = utils.now()
        time_range = self.config['time_range']
        from_time = utils.floor_time(now - time_range, time_range)

        d = self.backend.get_data(from_time=from_time)
        d.addCallback(self.handle_backend_response, now)
        return d
