from diamondash.widgets.chart import ChartWidgetConfig, ChartWidget


class HistogramWidgetConfig(ChartWidgetConfig):
    DEFAULTS = {}
    TYPE_NAME = 'histogram'


class HistogramWidget(ChartWidget):
    CONFIG_CLS = HistogramWidgetConfig
