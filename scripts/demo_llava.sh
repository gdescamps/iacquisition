#!/bin/bash
VENV=$1
pushd ..
CURRENT_DIR=`pwd`
echo ${CURRENT_DIR}
export PYTHONPATH=`pwd`:`pwd`/llava

streamlit run ./iacquisition/demo.py

popd
