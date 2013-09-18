#!/bin/sh

BINS='grunt bower'
PROJECT_ROOT=$(cd "`dirname $0`/.."; pwd)
NODE_BIN_DIR=$PROJECT_ROOT/node_modules/.bin

if [ -n $VIRTUAL_ENV ]; then
  for bin in $BINS
  do
    ln -si $NODE_BIN_DIR/$bin $VIRTUAL_ENV/bin/$bin
  done
fi

$NODE_BIN_DIR/bower install
