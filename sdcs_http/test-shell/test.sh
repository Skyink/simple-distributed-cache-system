#!/bin/bash

cs_num=$1
HOST_BASE=127.0.0.1
PORT_BASE=9526


port=$(( $PORT_BASE + $(shuf -i 1-$cs_num -n 1) ))
echo http://$HOST_BASE:$port