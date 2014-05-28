from diamondash.widgets.chart import ChartWidgetConfig, ChartWidget


class PieWidgetConfig(ChartWidgetConfig):
    DEFAULTS = {}
    TYPE_NAME = 'pie'

    @classmethod
    def parse(cls, config):
        config['bucket_size'] = config['time_range']
        return super(PieWidgetConfig, cls).parse(config)


class PieWidget(ChartWidget):
    CONFIG_CLS = PieWidgetConfig
