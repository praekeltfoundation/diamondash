#!/bin/bash

# A script to get the entire stack up and running on Ubuntu 12.04

WORKSPACE=~/workspace

# Required packages (assuming user has build-essential since this is geared
# towards developers).
sudo apt-get install memcached python-dev python-pip sqlite3 libcairo2 \
libcairo2-dev python-cairo

# Prep environment
mkdir -p $WORKSPACE
cd $WORKSPACE

# Virtual environment
virtualenv ve

# Pycairo
wget -c http://cairographics.org/releases/py2cairo-1.10.0.tar.bz2
tar -xvjf py2cairo-1.10.0.tar.bz2
cd py2cairo-1.10.0
./waf configure --prefix=${WORKSPACE}/ve
./waf build
./waf install

# Install carbon and graphite deps
cat > /tmp/graphite_reqs.txt << EOF
django==1.3.1
python-memcached
django-tagging
twisted
whisper==0.9.9
carbon==0.9.9
graphite-web==0.9.9
EOF
 
# Sadly graphite requires sudo
sudo ${WORKSPACE}/ve/bin/pip install -r /tmp/graphite_reqs.txt
 
# Configure carbon
cd /opt/graphite/conf/
sudo cp carbon.conf.example carbon.conf

# Storage schema
cd /opt/graphite/conf/
sudo cp storage-schemas.conf.example storage-schemas.conf 

# Make sure log dir exists for webapp
sudo mkdir -p /opt/graphite/storage/log/webapp
 
# Copy over the local settings file and initialize database
cd /opt/graphite/webapp/graphite/
sudo cp local_settings.py.example local_settings.py
sudo ${WORKSPACE}/ve/bin/python manage.py syncdb

# Start up carbon in background. Use './carbon-cache.py --debug start' to run
# in foreground.
cd /opt/graphite/bin
sudo ./carbon-cache.py start

# Generate some data. Can use system Python to run. Run in background.
cd $WORKSPACE
wget -c https://raw.github.com/graphite-project/graphite-web/master/examples/example-client.py
python example-client.py &

# Install diamondash
cd $WORKSPACE
git clone https://github.com/praekelt/diamondash
cd diamondash
${WORKSPACE}/ve/bin/python setup.py install

# Modify example dashboard to render the example client data
sed -i "s/howard/${HOSTNAME}/g" ${WORKSPACE}/diamondash/etc/dashboards/dashboard.example.yml

# Start up diamondash in background. Add --nodaemon after twistd to run in
# foreground.
${WORKSPACE}/ve/bin/twistd diamondash -c ${WORKSPACE}/diamondash/etc/ -p 8001

echo "Starting up Graphite's Django server. Once it is running you can navigate to Diamondash on http://localhost:8001"

# Start up Django last and in foreground, because runserver does not like being
# used with &. Run on port 8080 because diamondash example app dashboard
# assumes it.
cd /opt/graphite/webapp/graphite
sudo ${WORKSPACE}/ve/bin/python manage.py runserver 0.0.0.0:8080
