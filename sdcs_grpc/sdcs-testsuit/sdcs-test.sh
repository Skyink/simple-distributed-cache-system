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

which jq >/dev/null 2>&1 || {
	echo "Error: please install jq first."
	exit 3
}

PORT_BASE=9526
HOST_BASE=127.0.0.1
MAX_ITER=500
DELETED_KEYS=()
_DELETED_KEYS_GENERATED=0

PASS_PROMPT="\e[1;32mPASS\e[0m"
FAIL_PROMPT="\e[1;31mFAIL\e[0m"

function get_cs() {
	port=$(($PORT_BASE + $(shuf -i 1-$cs_num -n 1)))
	echo http://$HOST_BASE:$port
}

function get_key() {
	echo "key-$(shuf -i 1-$MAX_ITER -n 1)"
}

function gen_deleted_keys() {
	[[ $_DELETED_KEYS_GENERATED == 1 ]] && return 0

	local count=$((MAX_ITER / 10 * 3))

	while [[ ${#DELETED_KEYS[@]} -lt $count ]]; do
		local key="key-$(shuf -i 1-$MAX_ITER -n 1)"
		if ! [[ " ${DELETED_KEYS[@]} " =~ " ${key} " ]]; then
			DELETED_KEYS+=("$key")
		fi
	done

	_DELETED_KEYS_GENERATED=1
}

function gen_json_with_idx() {
	local idx=$1

	jq -n --arg key "key-$idx" --arg value "value $idx" '{($key): ($value)}'
}

function gen_json_with_key() {
	local idx=$(echo $key | cut -d- -f2)

	gen_json_with_idx $idx
}

function compare_json_for_key() {
	local key=$1
	local result=$2
	local expect=$3

	local value1=$(echo "$result" | jq -r ".\"$key\"" 2>/dev/null)
	local value2=$(echo "$expect" | jq -r ".\"$key\"" 2>/dev/null)

	[[ "$value1" = "$value2" ]]
}

function query_key() {
	local key=$1
	local exist=$2
	local response=$(curl -s -w "\n%{http_code}" $(get_cs)/$key)
	# everything but the last line. `head -n -1` breaks in macos, let's turn to sed trick.
	local result=$(echo "$response" | sed '$d')
	local status_code=$(echo "$response" | tail -n 1)

	if [[ $exist == 1 ]]; then
		local expect=$(gen_json_with_key $key)
		if [[ $status_code -ne 200 ]] || ! compare_json_for_key "$key" "$result" "$expect"; then
			echo -e "Error:\tInvalid response"
			echo -e "\texpect: 200 $expect"
			echo -e "\tgot: $status_code $result"
			return 1
		fi
	else
		if [[ $status_code -ne 404 ]]; then
			echo "Error: expect status code 404 but got $status_code"
			return 1
		fi
	fi
}

function test_set() {
	local i=1

	while [[ $i -le $MAX_ITER ]]; do
		status_code=$(curl -s -o /dev/null -w "%{http_code}" -XPOST -H "Content-type: application/json" -d "$(gen_json_with_idx $i)" $(get_cs))
		if [[ $status_code -ne 200 ]]; then
			echo "Error: expect status code 200 but got $status_code"
			return 1
		fi
		((i++))
	done
}

function test_get() {
	local count=$((MAX_ITER / 10 * 3))
	local i=0

	while [[ $i -lt $count ]]; do
		query_key $(get_key) 1 || return 1
		((i++))
	done
}

function test_delete() {
	gen_deleted_keys
	for key in "${DELETED_KEYS[@]}"; do
		local response=$(curl -XDELETE -s -w "\n%{http_code}" $(get_cs)/$key)
		# `head -n 1` works for delete actually. let's use sed for consistency.
		local result=$(echo "$response" | sed '$d')
		local status_code=$(echo "$response" | tail -n 1)
		local expect=1
		if [[ $status_code -ne 200 ]] || [[ "$result" != "$expect" ]]; then
			echo -e "Error:\tInvalid response"
			echo -e "\texpect: $status_code $expect"
			echo -e "\tgot: $status_code $result"
			return 1
		fi
	done
}

# need to check all keys to guarantee only appointed keys are removed.
function test_get_after_delete() {
	local key
	local exist
	local i=1
	while [[ $i -le $MAX_ITER ]]; do
		key=$(get_key)
		[[ " ${DELETED_KEYS[@]} " =~ " ${key} " ]] && exist=0 || exist=1

		query_key $key $exist || return 1

		((i++))
	done
}

function test_delete_after_delete() {
	for key in "${DELETED_KEYS[@]}"; do
		local response=$(curl -XDELETE -s -w "\n%{http_code}" $(get_cs)/$key)
		local result=$(echo "$response" | sed '$d')
		local status_code=$(echo "$response" | tail -n 1)
		if [[ $status_code -ne 200 ]] || [[ "$result" != "0" ]]; then
			echo -e "Error:\tInvalid response"
			echo -e "\texpect: 200 0"
			echo -e "\tgot: $status_code $result"
			return 1
		fi
	done
}

function run_test() {
	local test_function=$1
	local test_name=$2

	# echo "starting $test_name..."
	if $test_function; then
		echo -e "$test_name ...... ${PASS_PROMPT}"
		return 0
	else
		echo -e "$test_name ...... ${FAIL_PROMPT}"
		return 1
	fi
}

declare -a test_order=(
	"test_set"
	"test_get"
	"test_set again"
	"test_delete"
	"test_get_after_delete"
	"test_delete_after_delete"
)

declare -A test_func=(
	["test_set"]="test_set"
	["test_get"]="test_get"
	["test_set again"]="test_set"
	["test_delete"]="test_delete"
	["test_get_after_delete"]="test_get_after_delete"
	["test_delete_after_delete"]="test_delete_after_delete"
)

pass_count=0
fail_count=0

# NOTE: macos date does not support `date +%s%N`. Let's use the weird $TIMEFORMAT.
TIMEFORMAT="======================================
Run ${#test_order[@]} tests in %R seconds."

time {
	for testname in "${test_order[@]}"; do
		if run_test "${test_func[$testname]}" "$testname"; then
			((pass_count++))
		else
			((fail_count++))
		fi
	done
}

echo -e "\e[1;32m$pass_count\e[0m passed, \e[1;31m$fail_count\e[0m failed."
