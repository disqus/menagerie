#!/bin/bash
set -e

LICENSE=$1
DESTINATION=$2

if [[ ! $(grep -q __license__ $DESTINATION) ]]; then
    echo '__license__ = """' > $DESTINATION.new
    cat < $LICENSE >> $DESTINATION.new
    echo '"""' >> $DESTINATION.new
    echo '' >> $DESTINATION.new
    cat $DESTINATION >> $DESTINATION.new
    mv $DESTINATION.new $DESTINATION
fi
