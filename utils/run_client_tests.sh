#!/bin/sh

cd utils/client_test_maker
python make_tests.py "../../diamondash" > tests.html
mocha-phantomjs tests.html
rm tests.html
cd ../../
