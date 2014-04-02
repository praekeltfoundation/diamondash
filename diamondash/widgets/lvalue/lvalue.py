from itertools import takewhile

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.dynamic import DynamicWidgetConfig, DynamicWidget
from diamondash.backends import BadBackendResponseError


class LValueWidgetConfig(DynamicWidgetConfig):
    TYPE_NAME = 'lvalue'

    DEFAULTS = {
        'time_range': '1d',
        'default_value': 0,
        'align_to_start': False,
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
            'time_alignment': 'floor',
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

    def handle_backend_response(self, metric_data, until_time):
        if not metric_data:
            raise BadBackendResponseError(
                "LValueWidget '%s' received empty response from backend")

        datapoints = metric_data[0]['datapoints']
        from_time = until_time - self.config['time_range']
        prev_time = from_time - self.config['time_range']

        prev = {
            'x': prev_time,
            'y': self.config['default_value']
        }
        for n in takewhile(lambda d: d['x'] <= prev_time, datapoints):
            prev = n

        last = {
            'x': from_time,
            'y': self.config['default_value']
        }
        for n in takewhile(lambda d: d['x'] <= from_time, datapoints):
            last = n

        return {
            'from': from_time,
            'to': until_time,
            'last': last['y'],
            'prev': prev['y'],
        }

    def get_snapshot(self):
        time_range = self.config['time_range']

        if self.config['align_to_start']:
            until_time = utils.floor_time(utils.now(), time_range)
        else:
            until_time = utils.now()

        # ask for time since double the time range so we can compare with the
        # previous time range
        from_time = until_time - (time_range * 2)
        d = self.backend.get_data(from_time=from_time)
        d.addCallback(self.handle_backend_response, until_time)
        return d
