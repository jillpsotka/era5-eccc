#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate era5-env
cd ~/era5_for_arcc
DAY_OF_MONTH=$(date +"%-d")
MONTH=$(date +"%-m")
if [ $DAY_OF_MONTH -gt 10 ]; then
    python plots_mtd.py season ARCC True
    echo "done partial season normals"
    python plots_mtd.py season ARCC False
    echo "done full season normals"
fi