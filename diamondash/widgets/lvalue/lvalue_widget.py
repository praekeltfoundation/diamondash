import json
from pkg_resources import resource_string

from twisted.python import log
from twisted.web.template import XMLString

from diamondash import utils
from diamondash.widgets import Widget
from diamondash.backends.graphite import GraphiteBackend


class LValueWidget(Widget):

    __DEFAULTS = {'time_range': '1d'}
    __CONFIG_TAG = 'diamondash.widgets.lvalue.LValueWidget'

    MIN_COLUMN_SPAN = 2
    MAX_COLUMN_SPAN = 2

    MODEL = 'LValueWidgetModel'
    VIEW = 'LValueWidgetView'

    loader = XMLString(resource_string(__name__, 'template.xml'))

    def __init__(self, backend, time_range, **kwargs):
        super(LValueWidget, self).__init__(**kwargs)
        self.backend = backend
        self.time_range = time_range

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(LValueWidget, cls).parse_config(config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(config, cls.__DEFAULTS, defaults)

        # Set the bucket size to the passed in time range (for eg, if 1d was
        # the time range, the data for the entire day would be aggregated).
        time_range = utils.parse_interval(config['time_range'])
        config['time_range'] = time_range

        # We set the from param to double the bucket size. As a result,
        # graphite will return two datapoints for each metric: the previous
        # value and the last value.  The last and previous values will be used
        # to calculate the percentage increase.
        from_time = int(time_range) * 2

        # We have this set to use the Graphite backend for now, but the type
        # of backend could be made configurable in future
        config['backend'] = GraphiteBackend.from_config({
            'from_time': from_time,
            'metrics': [{
                'target': config.pop('target'),
                'bucket_size': time_range,
                'null_filter': 'zeroize',
            }]
        }, class_defaults)

        return config

    def process_backend_response(self, metric_data):
        """
        Accepts graphite render response data and performs the data processing
        and formatting necessary to have the data useable by lvalue widgets on
        the client side.
        """

        datapoints = []
        if not metric_data:
            log.msg(
                "LValueWidget '%s' received an empty response from backend."
                % self.title)
        else:
            datapoints = metric_data[0]['datapoints']

        prev, last = datapoints[-2:]

        prev_y, last_y = prev['y'] or 0, last['y'] or 0
        diff_y = last_y - prev_y

        percentage = (diff_y / prev_y) if prev_y != 0 else 0

        from_time = last['x'] or 0
        to_time = from_time + self.time_range - 1

        return json.dumps({
            'lvalue': last_y,
            'from': from_time,
            'to': to_time,
            'diff': diff_y,
            'percentage': percentage,
        })

    def handle_render_request(self, request):
        # In future, we could pass kwargs (such as different 'from' and 'to'
        # request parameters) to the backend and make two get_data() calls (two
        # requests to the backend). This would allow us to get lvalue data with
        # less of a burden on graphite.
        d = self.backend.get_data()

        d.addCallback(self.process_backend_response)
        return d
