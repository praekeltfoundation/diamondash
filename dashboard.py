"""Dashboard functionality for the diamondash web app"""

import re
import yaml
from unidecode import unidecode
from pkg_resources import resource_string, resource_stream
from twisted.web.template import Element, renderer, XMLFile


class Dashboard(Element):
    """Dashboard element for the diamondash web app"""

    loader = XMLFile(resource_stream(__name__, 'templates/dashboard.xml'))

    def __init__(self, config):
        self.config = self.parse_config(config)

    @classmethod 
    def parse_config(cls, config):
        if 'name' not in config:
            raise DashboardConfigError('Dashboard name not specified.')

        config['title'] = config['name']
        config['name'] = slugify(config['name'])

        widget_dict = {}
        for w_name, w_config in config['widgets'].items():
            if 'metrics' not in w_config: 
                raise DashboardConfigError(
                    'Widget "%s" needs metric(s).' % (w_name,))

            if 'title' not in w_config: 
                w_config['title'] = w_name

            w_name = slugify(w_name)

            if 'type' not in w_config:
                w_config['type'] = 'graph' 

            if 'null_filter' not in w_config:
                w_config['null_filter'] = 'skip'

            widget_dict.update({w_name: w_config})

        # update widget dict to dict with slugified widget names
        config['widgets'] = widget_dict

        return config


    @classmethod
    def from_config_file(cls, filename):
        """Loads dashboard information from a config file"""
        # TODO check and test for invalid config files

        try: 
            config = yaml.safe_load(resource_string(__name__, filename))
        except IOError:
            raise DashboardConfigError('File %s not found.' % (filename,))

        return cls(config)

    def get_widgets(self, w_name):
        """Returns a widget using the passed in widget name"""
        return self.config['widgets'][w_name]

    def get_widget_targets(self, w_name):
        """Returns a widget using the passed in widget name"""
        return self.config['widgets'][w_name]['metrics'].values()

    @renderer
    def widget(self, request, tag):
        for w_name, config in self.config['widgets'].items():
            new_tag = tag.clone()

            if 'type' not in config:
                config['type'] = 'graph'
            class_attr_list = ['widget', config['type']]
            class_attr = ' '.join('%s' % attr for attr in class_attr_list)

            style_attr_dict = {}
            for style_key in ['width', 'height']:
                if style_key in config:
                    style_attr_dict[style_key] = config[style_key]
            style_attr = '; '.join('%s: %s' % item for item in style_attr_dict.items())


            new_tag.fillSlots(widget_title_slot=config['title'],
                              widget_style_slot=style_attr,
                              widget_class_slot=class_attr,
                              widget_id_slot=w_name)
            yield new_tag


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text):
    """Slugifies the passed in text"""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return '-'.join(result)


class DashboardConfigError(Exception):
    """Raised if a config file does not contain a compulsory attribute"""
