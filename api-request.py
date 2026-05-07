''' api request to query the public copernicus ERA5 database.
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview 
gets most recent data (5 days ago - sometimes incomplete) as well as 6 days ago (overwrites yesterday's partial file)
Grib files get downloaded, turned into netcdf, processed a bit, and saved as netcdf.
2m temperature and total precip, hourly, for all of Canada. 
'''

import cdsapi
import datetime
from datetime import timedelta
import os
import cfgrib
import xarray as xr
import glob
from setup import paths, vars_for_api


pathname_data = paths['pathname_data']
lons = vars_for_api['lons']
lats = vars_for_api['lats']

today = datetime.date.today()
print('Starting job',today)
files_downloaded = 0

# first check if we are missing any files from the past 5-10 days
dataset = "reanalysis-era5-single-levels"
for i in range(5,7):  # download 5 days ago (partial) and 6 days ago (full to overwrite yesterday's partial)
    day = today - timedelta(days=i)
    filename = pathname_data+"daily/era5-"+day.strftime("%Y-%m-%d")+".nc"
    print("Retrieving "+day.strftime("%Y-%m-%d")+" from Copernicus CDS...")
    request = {
        "product_type": ["reanalysis"], # need this line for era-5, not era5-land
        "variable": [
            "2m_temperature",
            "total_precipitation"
        ],
        "year": [day.strftime('%Y')],
        "month": [day.strftime('%m')],
        "day": [day.strftime('%d')],
        "time": [
            "00:00", "01:00", "02:00",
            "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00",
            "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00",
            "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00",
            "21:00", "22:00", "23:00"
        ],
        "data_format": "grib",
        "download_format": "unarchived",
        "area": vars_for_api['area_era5']
    }

    client = cdsapi.Client()
    filename_grib = "temp/era5-"+day.strftime("%Y-%m-%d")+".grib"
    try:
        client.retrieve(dataset, request,filename_grib)  # downloads the grib file
    except:
        print("Not available yet")  # go to next day if file isn't there
        print('\n')
        continue

    # convert grib to .nc, chop it, and convert precip time axis to match temp
    ds_raw = cfgrib.open_datasets(filename_grib)
    T = ds_raw[0]
    P = ds_raw[1]
    # if len(T.time) != 24:  # don't want to save partial days
    #     for f in glob.glob(filename_grib+'*'):  # delete grib file and index file
    #         os.remove(f)
    #     continue
    # convert time and step into valid_time dimension
    P_converted = xr.Dataset({"tp":(["time","latitude","longitude"],P.tp.values.reshape((len(P.time)*len(P.step),len(P.latitude),len(P.longitude))))},
                {"time":("time",P.valid_time.values.flatten()),"latitude":P.latitude,"longitude":P.longitude})
    P_converted['tp'] = P_converted['tp'] * 1000 # m to mm
    P_converted = P_converted.dropna(dim='time')
    ds_full = xr.merge([T,P_converted])
    ds_full = ds_full.sel(longitude=lons,latitude=lats).drop_vars(['valid_time','step','surface','number'])
    start = str(ds_full.time.values[0])[:10]

    if len(ds_full.longitude) != 0:
        ds_full.to_netcdf(filename)
        files_downloaded += 1
        for f in glob.glob(filename_grib+'*'):  # delete grib file and index file
            os.remove(f)

print('Success',today,', ',files_downloaded,'file(s) downloaded.\n')