from diamondash.config import ConfigError
from diamondash.widgets.chart import ChartWidgetConfig, ChartWidget


class HistogramWidgetConfig(ChartWidgetConfig):
    DEFAULTS = {}
    TYPE_NAME = 'histogram'

    @classmethod
    def parse(cls, config):
        if 'target' not in config:
            raise ConfigError("All HistogramWidgets need a target")

        config['metrics'] = [{
            'name': config.get('name', config.get('title')),
            'target': config.pop('target')
        }]
        return super(HistogramWidgetConfig, cls).parse(config)


class HistogramWidget(ChartWidget):
    CONFIG_CLS = HistogramWidgetConfig
