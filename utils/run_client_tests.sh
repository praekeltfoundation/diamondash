#!/bin/sh

cd "diamondash"
CLIENT_TESTS=`find -name "*.test.js" | while read f; do echo "${f%.js}"; done`

export NODE_ENV=test 
export NODE_PATH=$NODE_PATH:"`pwd`/widgets":"`pwd`/public/js/"

mocha \
    --require '../utils/client-test-helper.js' \
	--reporter spec \
	--ui bdd \
	--colors \
	--recursive \
	$CLIENT_TESTS
