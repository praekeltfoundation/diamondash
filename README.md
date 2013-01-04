diamondash
==========

Dashboard for how we use Graphite.

How to install
--------------
`
python setup.py install
`

How to configure
----------------
`diamondash.yml` is used to configure the web server and global dashboard defaults. Each file in `dashboards/` contains a configuration for a particular dashboard. See `etc/` for an example of how diamondash can be configured.

How to run
----------
Diamondash is run as a twisted plugin:

`
twistd diamondash -c <CONFIG_DIR> -p <PORT>
`

For usage with supervisord, an example supervisord config file can be found in `etc/`.
