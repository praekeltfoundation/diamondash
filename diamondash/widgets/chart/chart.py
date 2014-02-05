from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.dynamic import DynamicWidgetConfig, DynamicWidget


class ChartWidgetConfig(DynamicWidgetConfig):
    DEFAULTS = {
        'time_range': '1d',
        'bucket_size': '1h',
        'align_to_start': False,
    }

    TYPE_NAME = 'chart'

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    @classmethod
    def parse(cls, config):
        super(ChartWidgetConfig, cls).parse(config)

        if 'metrics' not in config:
            raise ConfigError(
                "Chart widget '%s' needs metrics." % config['name'])

        config['time_range'] = utils.parse_interval(config['time_range'])
        config['bucket_size'] = utils.parse_interval(config['bucket_size'])

        config['backend'].update({
            'bucket_size': config['bucket_size'],
            'metrics': [cls.parse_metric(m) for m in config.pop('metrics')],
        })

        if 'null_filter' in config:
            config['backend']['null_filter'] = config.pop('null_filter')

        backend_config_cls = cls.for_type(config['backend']['type'])
        config['backend'] = backend_config_cls(config['backend'])
        config['metrics'] = config['backend']['metrics']

        return config

    @classmethod
    def parse_metric(cls, config):
        """
        Parses a metric config given in a graph config into a config useable by
        the backend.
        """
        if 'name' not in config:
            raise ConfigError('Every chart metric needs a name.')

        name = config.pop('name')
        config['title'] = config.setdefault('title', name)
        config['name'] = utils.slugify(name)

        return config


class ChartWidget(DynamicWidget):
    CONFIG_CLS = ChartWidgetConfig

    def process_backend_response(self, metric_data):
        for metric in metric_data:
            # x values are converted to milliseconds for client
            metric['datapoints'] = [{
                'x': d['x'],
                'y': d['y']
            } for d in metric['datapoints']]

        output_metric_data = [{
            'id': m['id'],
            'datapoints': m['datapoints'],
        } for m in metric_data]

        return {'metrics': output_metric_data}

    def get_snapshot(self):
        time_range = self.config['time_range']
        if self.config['align_to_start']:
            from_time = utils.floor_time(utils.now(), time_range)
        else:
            from_time = utils.relative_to_now(-time_range)

        d = self.backend.get_data(from_time=from_time)
        d.addCallback(self.process_backend_response)
        return d
