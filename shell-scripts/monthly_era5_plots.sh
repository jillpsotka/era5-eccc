#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate era5-env
cd ~/era5_for_arcc
python plots.py month ARCC
