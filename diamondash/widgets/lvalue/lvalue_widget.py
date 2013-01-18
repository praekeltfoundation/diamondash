import json
from pkg_resources import resource_string

from twisted.web.template import XMLString

from diamondash import utils
from diamondash.exceptions import ConfigError
from diamondash.widgets.graphite import GraphiteWidget


class LValueWidget(GraphiteWidget):
    loader = XMLString(resource_string(__name__, 'template.xml'))

    DEFAULTS = {'time_range': '1h'}

    STYLESHEETS = ('lvalue/style.css',)
    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    MODEL = ('lvalue/lvalue-widget', 'LValueWidgetModel')
    VIEW = ('lvalue/lvalue-widget', 'LValueWidgetView')

    def __init__(self, **kwargs):
        super(LValueWidget, self).__init__(**kwargs)
        self.target = kwargs['target']
        self.time_range = kwargs['time_range']

    @classmethod
    def parse_config(cls, config, defaults={}):
        """Parses the lvalue widget config, altering it where necessary."""
        config = super(LValueWidget, cls).parse_config(config, defaults)

        config = dict(cls.DEFAULTS, **config)
        config = utils.insert_defaults_by_key(
            'diamondash.widgets.lvalue.LValueWidget', config, defaults)

        target = config.get('target', None)
        if target is None:
            raise ConfigError(
                "LValue widget %s needs a metric target" % config['name'])

        # Set the bucket size to the passed in time range (for eg, if 1d was
        # the time range, the data for the entire day would be aggregated).
        time_range = utils.parse_interval(config['time_range'])
        wrapped_target = cls.format_metric_target(target, time_range)
        config['time_range'] = time_range

        # Set the from param to double the bucket size. As a result, graphite
        # will return two datapoints for each metric: the previous value and
        # the last value. The last and previous values will be used to
        # calculate the percentage increase.
        from_param = int(time_range) * 2

        config['request_url'] = cls.build_request_url(
            config['graphite_url'], [wrapped_target], from_param)

        return config

    def build_render_response(self, datapoints):
        prev, last = datapoints[-2:]

        prev_y, last_y = prev[0] or 0, last[0] or 0
        diff_y = last_y - prev_y

        percentage = (diff_y / prev_y) * 100 if prev_y != 0 else 0
        percentage = "{0:.0f}%".format(percentage)

        last_y = utils.format_number(last_y)
        diff_y = "%s%s" % ('+' if diff_y > 0 else '',
                           utils.format_number(diff_y))

        time = last[1] or 0
        from_time = utils.format_time(time)
        to_time = utils.format_time(time + self.time_range - 1)

        return json.dumps({
            'lvalue': last_y,
            'from': from_time,
            'to': to_time,
            'diff': diff_y,
            'percentage': percentage,
        })

    def handle_graphite_render_response(self, data):
        """
        Accepts graphite render response data and performs the data
        processing and formatting necessary to have the data useable by lvalue
        widgets on the client side.
        """
        target_data = utils.find_dict_by_item(data, 'target', self.target)
        if target_data is None:
            # TODO: log?
            return "{}"

        return self.build_render_response(target_data['datapoints'])
