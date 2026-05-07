#!/bin/bash
eval "$(conda shell.bash hook)"
conda activate era5-env
cd ~/era5_for_arcc
DAY_OF_MONTH=$(date +"%-d")
MONTH=$(date +"%-m")
if [ $DAY_OF_MONTH -gt 24 ]; then
    python plots_mtd.py month ARCC False
    echo "done full month normals"
elif [[ $MONTH -eq 2 && $DAY_OF_MONTH -gt 21 ]]; then
    python plots_mtd.py month ARCC False
    echo "done full month normals - february"
fi
if [ $DAY_OF_MONTH -gt 10 ]; then
    python plots_mtd.py month ARCC True
    echo "done partial month normals"
fi