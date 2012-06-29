"""Dashboard functionality for the diamondash web app"""

from twisted.web.template import Element, renderer, XMLFile


class Dashboard(Element):
    """Dashboard element for the diamondash web app"""

    loader = XMLFile('templates/dashboard.xml')

    def __init__(self, config_filename=None, name=None, widget_config=None):
        if config_filename is not None:
            self.read_config_file(config_filename)
        else:
            self.name = name
            self.widget_config = widget_config

    def read_config_file(self, config_filename):
        """Loads dashboard information from a config file"""
        # TODO load from config file
        # TODO allow mulitple dashboards (instead of 'test_dashboard')
        self.name = 'test-dashboard'
        self.widget_config = {
            'random-count-sum': {
                'title': 'Sum of random count',
                'type': 'graph',
                'metric': 'vumi.random.count.sum',
                'width': '300px',
                'height': '150px'
            },
            'random-timer-average': {
                'title': 'Average of random timer',
                'type': 'graph',
                'metric': 'vumi.random.timer.avg'
            }
        }

    @renderer
    def widget(self, request, tag):
        for name, config in self.widget_config.items():
            new_tag = tag.clone()
            class_attr = 'widget'
            style_attr = ''

            # TODO use graph as default type
            if config['type'] == 'graph':
                class_attr += ' graph'

            style_attr_dict = {}
            for style_key in ['width', 'height']:
                if style_key in config:
                    style_attr_dict[style_key] = config[style_key]
            style_attr = ';'.join('%s %s' % \
                item for item in style_attr_dict.items())

            new_tag.fillSlots(widget_title_slot=config['title'],
                              widget_style_slot=style_attr,
                              widget_class_slot=class_attr,
                              widget_id_slot=name)
            yield new_tag
