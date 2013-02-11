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

Testing and Development
-----------------------
To run the server-side tests:

`
trial diamondash
`

For development and testing of the client-side code, you will need [node.js](http://nodejs.org/). With node.js on your system, install the client-side dev dependencies with:

`
npm install
`

To run (client and server)-side tests:

`
./utils/run_tests.sh
`

To run client-side tests:

`
./utils/grunt test
`

For client-side development, a build step is required. To watch and build on
changes:

`
./utils/grunt watch
`

To only build when changes have been made:

`
./utils/grunt
`
