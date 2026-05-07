#!/bin/bash
for i in /home/psotkaj/clim4/era5-data/from_ruping/20**/era5_single_level*; do
    python chop_era5.py $i
done