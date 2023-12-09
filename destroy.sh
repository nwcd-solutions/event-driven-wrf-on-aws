#!/bin/bash 

cd back-end/
. .venv/bin/activate
cdk destroy --force
