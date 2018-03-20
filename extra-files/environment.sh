#!/bin/bash
export DEBUG="True"
export STARTUP_SIGNUP_TABLE="gsg-signup-table"
export AWS_REGION="eu-west-1"
printenv | grep "DEBUG\|STARTUP_SIGNUP_TABLE\|AWS_REGION"
