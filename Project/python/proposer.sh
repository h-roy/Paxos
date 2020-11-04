#!/bin/bash
docker run -e APP_ROLE=proposer -e APP_MULTICAST_PORT=5000 -e APP_MULTICAST_ADDR=239.0.0.1 -e ID=$1 da1-py