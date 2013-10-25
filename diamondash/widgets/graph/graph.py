from diamondash.widgets.chart import ChartWidgetConfig, ChartWidget


class GraphWidgetConfig(ChartWidgetConfig):
    DEFAULTS = {
        'dotted': False,
        'smooth': False,
    }

    TYPE_NAME = 'graph'


class GraphWidget(ChartWidget):
    CONFIG_CLS = ChartWidgetConfig
