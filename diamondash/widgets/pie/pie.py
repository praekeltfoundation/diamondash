from diamondash.widgets.chart import ChartWidgetConfig, ChartWidget


class PieWidgetConfig(ChartWidgetConfig):
    DEFAULTS = {}
    TYPE_NAME = 'pie'


class PieWidget(ChartWidget):
    CONFIG_CLS = PieWidgetConfig
