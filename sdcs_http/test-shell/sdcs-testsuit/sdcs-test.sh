#!/bin/bash

if [[ $# -ne 1 ]]; then
	echo "Usage:"
	echo "$0 {cache server number}"
	exit 1
fi

cs_num=$1

# TODO: should also set upperbound next year.
[[ $cs_num -le 2 ]] && {
	echo "Error: cache server should be more than 3 ($cs_num provided)"
	exit 2
}

PORT_BASE=9526
HOST_BASE=127.0.0.1
MAX_ITER=500

function get_cs() {
	port=$(( $PORT_BASE + $(shuf -i 1-$cs_num -n 1) ))
	echo http://$HOST_BASE:$port
}

function get_key() {
	echo "key-$(shuf -i 1-$MAX_ITER -n 1)"
}

function test_set() {
	local i=1
	while [[ $i -le $MAX_ITER ]]; do
		curl -XPOST -H "Content-type: application/json" -d "{\"key-$i\": \"value $i\"}" $(get_cs) 
		((i++))
	done
}

function test_get() {
	local count=$(( MAX_ITER / 10 ))
	local i=0
	while [[ $i -lt $count ]]; do
		curl $(get_cs)/$(get_key)
		((i++))
	done
}

function test_delete() {
	local count=$(( MAX_ITER / 10 * 9 ))
	local i=0
	while [[ $i -lt $count ]]; do
		curl -XDELETE $(get_cs)/$(get_key)
		((i++))
	done
}

test_set
test_get
test_set
test_delete
test_get
