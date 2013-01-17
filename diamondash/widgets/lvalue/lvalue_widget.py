from diamondash import utils
from diamondash.exceptions import ConfigError
from diamondash.widgets.graphite import GraphiteWidget


class LValueWidget(GraphiteWidget):
    DEFAULTS = {'time_range': '1h'}

    STYLESHEETS = ('lvalue/style.css',)
    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    MODEL = ('lvalue/lvalue-widget', 'LValueWidgetModel')
    VIEW = ('lvalue/lvalue-widget', 'LValueWidgetView')

    def __init__(self, **kwargs):
        super(LValueWidget, self).__init__(kwargs)

    @classmethod
    def parse_config(cls, config, defaults={}):
        """Parses the lvalue widget config, altering it where necessary."""
        config = super(GraphiteWidget, cls).parse_config(config, defaults)

        config = utils.insert_defaults_by_key(__name__, config, defaults)
        config = dict(cls.DEFAULTS, **config)

        target = config.get('metric', None)
        if target is None:
            raise ConfigError(
                "LValue widget %s needs a metric" % config['name'])

        # Set the bucket size to the passed in time range (for eg, if 1d was
        # the time range, the data for the entire day would be aggregated).
        bucket_size = utils.parse_interval(config['time_range'])
        target = cls.format_metric_target(target, bucket_size)

        # Set the from param to double the bucket size. As a result, graphite
        # will return two datapoints for each metric: the previous value and
        # the last value. The last and previous values will be used to
        # calculate the percentage increase.
        from_param = int(bucket_size) * 2

        config['request_url'] = cls.build_request_url(config['graphite_url'],
                                                      [target], from_param)

        return config

    def handle_render_request(self, request):
        pass
