from mock import Mock


def stub_from_config(cls):
    cls.from_config = Mock(
        side_effect=lambda config, class_defaults: (config, class_defaults))
