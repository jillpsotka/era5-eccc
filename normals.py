# calculating and saving 30-year normals for each grid point
# path names and years to use come from setup.py
# saves the normals file to the pathname_data location

import numpy as np
import xarray as xr
import glob
import pandas as pd
from setup import paths, vars


pathname = paths['pathname']
pathname_data = paths['pathname_data']
years = vars['normals_years']
months = ['01','02','03','04','05','06','07','08','09','10','11','12']
list_of_arrays = []

# too heavy if we do it all at once; split up by month
for m in months:
    filepath = pathname_data+'monthly/*-'+m+'.nc'
    files = glob.glob(filepath)

    # gross way of only selecting files for the normals years
    for f in reversed(range(len(files))):
        if not np.isin(files[f][-10:-6],years):  # index of the year in the file name. should be ok to have hard coded as long as file naming convention doesn't change
            files.pop(f)
    if len(files) != 30:
        raise ValueError('WARNING! 30 years of data not detected for normals calculations')
    
    files.sort()
    ds1 = xr.open_dataset(files[0])
    for file in files[1:]:
        ds2 = xr.open_dataset(file)
        ds1 = xr.merge([ds1,ds2])

    # now group by day of year to get daily normals over the 30 years
    month_idx = pd.MultiIndex.from_arrays([ds1['time.month'].values, ds1['time.day'].values],names=['month','day'])
    ds1.coords['month_day'] = ('time', month_idx)
    ds1 = ds1.groupby('month_day').mean()
    ds1 = ds1.reset_index("month_day")
    list_of_arrays.append(ds1)
    print(m)
normals = xr.concat(list_of_arrays,dim='month_day')
normals.to_netcdf(pathname_data+"normals-"+str(years[0])+'-'+str(years[-1])+".nc")