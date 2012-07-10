"""Dashboard functionality for the diamondash web app"""

import re

import json
import yaml
from unidecode import unidecode
from pkg_resources import resource_stream
from twisted.web.template import Element, renderer, XMLFile, Tag
from exceptions import ConfigError


DEFAULT_WIDGET_TYPE = 'graph'
DEFAULT_NULL_FILTER = 'skip'
DEFAULT_RENDER_PERIOD = 3600
DEFAULT_BUCKET_SIZE = 300
DEFAULT_DIFF_SIZE = 1800


class Dashboard(Element):
    """Dashboard element for the diamondash web app"""

    # keys to metric attributes needed by client
    CLIENT_METRIC_KEYS = ['target', 'title', 'color']

    loader = XMLFile(resource_stream(__name__, 'templates/dashboard.xml'))

    def __init__(self, config, client_config=None):
        self.config, self.client_config = self.parse_config(
            config, client_config)
        self.client_config['dashboardName'] = config['name']

    @classmethod
    def format_metric_target(cls, target, bucket_size):
        bucket_size = '%ss' % (str(bucket_size),)
        agg_method = "avg"
        metric_fn = target.rstrip(')').split('.')[-1]
        if target.startswith('integral('):
            agg_method = 'max'
        elif metric_fn in ('max', 'min', 'sum'):
            agg_method = metric_fn
        return 'summarize(%s, "%s", "%s")' % (target, bucket_size, agg_method)

    @classmethod
    def parse_config(cls, config, client_config=None):
        if 'name' not in config:
            raise ConfigError('Dashboard name not specified.')

        config['title'] = config['name']
        config['name'] = slugify(config['name'])

        config.setdefault('null_filter', DEFAULT_NULL_FILTER)
        config.setdefault('render_period', DEFAULT_RENDER_PERIOD)
        config.setdefault('diff_size', DEFAULT_DIFF_SIZE)
        config.setdefault('bucket_size', DEFAULT_BUCKET_SIZE)

        if client_config is None:
            client_config = {}

        client_config.setdefault('widgets', {})

        widget_dict = {}
        client_widget_dict = {}
        for w_name, w_config in config['widgets'].items():
            if 'metrics' not in w_config:
                raise ConfigError('Widget "%s" needs metric(s).' % (w_name,))

            w_config.setdefault('title', w_name)
            w_name = slugify(w_name)
            w_config.setdefault('type', DEFAULT_WIDGET_TYPE)
            w_config.setdefault('null_filter', config['null_filter'])
            w_config.setdefault('render_period', config['render_period'])
            w_config.setdefault('diff_size', config['diff_size'])
            bucket_size = w_config.setdefault('bucket_size', config['bucket_size'])

            client_widget_dict = client_config['widgets'].setdefault(w_name, {})
            client_metric_config = client_widget_dict.setdefault('metrics', {})

            metric_dict = {}
            for m_name, m_config in w_config['metrics'].items():
                if 'target' not in m_config:
                    raise ConfigError(
                        'Widget "%s" needs a target for metric "%s".'
                        % (w_name, m_name))

                m_config['original_target'] = m_config['target']
                m_config['target'] = cls.format_metric_target(
                    m_config['target'], bucket_size)
                m_config.setdefault('null_filter', w_config['null_filter'])

                m_config.setdefault('title', m_name)
                m_name = slugify(m_name)
                metric_dict[m_name] = m_config
                m_client_config = dict(
                    (k, m_config[k])
                    for k in cls.CLIENT_METRIC_KEYS if k in m_config)
                client_metric_config[m_name] = m_client_config

            w_config['metrics'] = metric_dict
            widget_dict[w_name] = w_config

        # update widget dict to dict with slugified widget names
        config['widgets'] = widget_dict

        return config, client_config

    @classmethod
    def from_config_file(cls, filename, client_config=None):
        """Loads dashboard information from a config file"""
        # TODO check and test for invalid config files

        try:
            config = yaml.safe_load(open(filename))
        except IOError:
            raise ConfigError('File %s not found.' % (filename,))

        return cls(config, client_config)

    def get_widget_config(self, w_name):
        """Returns a widget using the passed in widget name"""
        return self.config['widgets'][w_name]

    @renderer
    def widget_renderer(self, request, tag):
        for w_name, w_config in self.config['widgets'].items():
            new_tag = tag.clone()

            class_attr_list = ['widget', '%s-widget' % (w_config['type'],)]
            class_attr = ' '.join('%s' % attr for attr in class_attr_list)

            style_attr_dict = {}
            for style_key in ['width', 'height']:
                if style_key in w_config:
                    style_attr_dict[style_key] = w_config[style_key]
            style_attr = ';'.join('%s: %s' % item
                                  for item in style_attr_dict.items())

            # to not break the template with invalid types
            widget_element = ''

            if w_config['type'] == 'graph':
                widget_element = GraphWidget()

            new_tag.fillSlots(widget_title_slot=w_config['title'],
                              widget_style_slot=style_attr,
                              widget_class_slot=class_attr,
                              widget_id_slot=w_name,
                              widget_element_slot=widget_element)
            yield new_tag

    @renderer
    def config_script(self, request, tag):
        # TODO fix injection vulnerability

        #serialize client vars into a json string ready for javascript
        client_config_str = 'var config = %s' % (
            json.dumps(self.client_config),)

        if self.client_config is not None:
            tag.fillSlots(client_config=client_config_str)
        return tag


class GraphWidget(Element):
    """GraphElement element that resides in a Dashboard element"""

    loader = XMLFile(resource_stream(__name__, 'templates/graph_widget.xml'))


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text):
    """Slugifies the passed in text"""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return '-'.join(result)
