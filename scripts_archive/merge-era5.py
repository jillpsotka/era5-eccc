# this script takes era files that are separated by year and slices and groups them into longitude chunks instead
# (necessary due to era5 downloading limitations - easier to group by year when downloading)

import numpy as np
import xarray as xr
import os
import glob
import sys
import cfgrib
import warnings
warnings.filterwarnings("ignore")

pathname = "C:\\Users\\PsotkaJ\\Projects\\era5_for_arcc\\"
var = 'P'  #'T'
if var == 'P':
    x = 1
else:
    x = 0
# T and P have different time values (P has steps) so we have to separate them into 2 datasets

# find all era5 files in the folder
filepath = pathname+'data\\era5-P-lons-*.nc'
files = glob.glob(filepath)
files.sort()

lon_slices = [slice(-62,-50),slice(-74,-62),slice(-86,-74),slice(-98,-86),
            slice(-110,-98),slice(-122,-110),slice(-134,-122),slice(-145,-134)]
titles = ["-50_-62","-62_-74","-74_-86","-86_-98","-98_-110","-110_-122",
        "-122_-134","-134_-145"]  # if i have time could make these cleaner and automated

# to keep file size down, split the domain into chunks via longitude.
# full domain is [85,-145,53,-50].
# split into 8? longitudes -50, -62, -74, -86, -98, -110, -122, -134, -145.
# each 30-year file will be about 6 gb

# for f in files:
#     ds1 = cfgrib.open_datasets(f)[x]  #xr.open_dataset(files[0])
#     if var == 'P':  # convert time and step into valid_time dimension
#         ds1 = xr.Dataset({"tp":(["time","latitude","longitude"],ds1.tp.values.reshape((len(ds1.time)*len(ds1.step),len(ds1.latitude),len(ds1.longitude))))},
#                     {"time":("time",ds1.valid_time.values.flatten()),"latitude":ds1.latitude,"longitude":ds1.longitude})
#         ds1['tp'] = ds1['tp'] * 1000 # m to mm
#         ds1 = ds1.dropna(dim='time')
#     for i in range(len(lon_slices)):
#         ds = ds1.sel(longitude=lon_slices[i])
#         start = str(ds.time.values[0])[:10]
#         end = str(ds.time.values[-1])[:10]
#         if len(ds.longitude) != 0:
#             ds.to_netcdf("data\\era5-"+var+"-lons"+titles[i]+"from"+start+'-'+end+".nc")

# print('done splitting into lon chunks')

# concatenation of years for each lon chunk
for j in range(len(titles)):
    filepath = pathname+"era5-"+var+"-lons"+titles[j]+'*.nc'
    files = glob.glob(filepath)
    files.sort()
    T = xr.open_dataset(files[0])

    for f in files[1:]:
        T1 = xr.open_dataset(f)
        T = xr.concat([T,T1],dim="time")

        T = T.sortby('time')
        T = T.drop_duplicates('time')

    start = str(T.time.values[0])[:10]
    end = str(T.time.values[-1])[:10]

    filenameT = 'era5-'+var+'-lons'+titles[j]+"from"+start+'-'+end+'.nc'
    T.to_netcdf(filenameT)

print('done concatenating')