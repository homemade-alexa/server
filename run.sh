#!/bin/bash

d=`dirname $0`
source $d/venv/bin/activate
python3 $d/src/server.py

