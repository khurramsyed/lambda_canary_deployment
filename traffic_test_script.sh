#!/bin/bash
URL= https://o2vcly5ftb.execute-api.eu-west-2.amazonaws.com/qa
while true; do
	echo "$(date +%F_%H%M%S) - $(curl -s $URL)"
	sleep 5
done
