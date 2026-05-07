#!/bin/bash
cd /home/jpsotka/clim4/era5-data/from_ruping
for yr in $(seq 1972 1999); do
    for mo in {01..12}; do
        yr += $mo;
        wget -r -nH --cut-dirs=7 --no-parent --reject="index.html*" https://web.science.gc.ca/~rum001/natlabw/projects/era5/nc/sl/hourly/$yr$mo/
    done
done