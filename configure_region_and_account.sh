#!/bin/bash
export REGION=$(aws configure get region)
export ACCOUNT=$(aws sts get-caller-identity | jq -r .Account)
