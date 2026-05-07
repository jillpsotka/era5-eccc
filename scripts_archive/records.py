# first we want records of warmest/coldest and wettest/driest DJF seasons

import numpy as np
import xarray as xr
import glob
from datetime import datetime
import geopandas as gp
import regionmask
from setup import paths, vars


def daily_to_monthly():
    # merge daily files into monthly
    # can only run this for months that are completed
    years = range(2024,2025)
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']  # if not doing full year, need to include the current month in this list
    for i in range(len(years)):
        for j in range(len(months)):
            filepath = pathname_data+'daily/era5-'+str(years[i])+'-'+months[j]+'*.nc'
            files = glob.glob(filepath)
            files.sort()
            # now add in the first day of the next month, so we can resample hourly -> daily from 06Z-06Z
            if j < len(months)-1:
                filepath_next_month = pathname_data+'daily/era5-'+str(years[i])+'-'+months[j+1]+'-01.nc'
            elif months[j] == '12': # december
                filepath_next_month = pathname_data+'daily/era5-'+str(years[i]+1)+'-'+months[0]+'-01.nc'
            if datetime.today().year != years[i] and datetime.today().month != int(months[j]):  # if current month, don't try to add next month's first day
                files.append(filepath_next_month)
            ds1 = xr.open_dataset(files[0])
            ds1 = ds1.sel(longitude=lons,latitude=lats)
            for f in files[1:]:
                ds = xr.open_dataset(f)
                ds = ds.sel(longitude=lons,latitude=lats)
                ds1 = xr.concat([ds1,ds],dim='time')

            T = ds1.t2m.resample(time="1D",origin=datetime(1901,1,1,6)).mean()  # resample hourly -> daily from 06Z-06Z
            P = ds1.tp.resample(time="1D",origin=datetime(1901,1,1,7)).sum()  # resample hourly -> daily from 06Z-06Z
            # we want P from 07Z-07Z so that when we take 1 climatological day (06Z-06Z), P represents total precip that fell on that day
            P['time'] = P.time-int(1*60*60*1E9) # shift time axis to match T
            ds1 = xr.merge([T,P])
            ds1 = ds1.sel(time=ds1.time.dt.month.isin([int(months[j])]))
            ds1.to_netcdf(pathname_data+'monthly/'+str(years[i])+'-'+months[j]+'.nc')
        print('done',years[i])


def get_szn_vals(season='DJF'):
    if season == 'DJF':
        mos = ['12','01','02']
    else:
        raise ValueError('havent coded for other seasons yet')
    years = range(2020,2025)
    T_list = []
    P_list = []

    for i in range(len(years)): # for each season
        # concat files for desired season and surrounding months so that time zone stuff doesn't lose us data
        if season != 'DJF':
            filepath = pathname_data+'ERA5_1991-2020/era5-T-'+str(years[i])+'-'+mos[0]+'.nc'
            year_start = str(years[i])
        else:  # if it's winter we have to go back a year to get december
            filepath = pathname_data+'ERA5_1991-2020/era5-T-'+str(years[i]-1)+'-'+mos[0]+'.nc'
            year_start = str(years[i]-1)

        ds1 = xr.open_dataset(filepath)
        for j in range(1,len(mos)):
            # if season == 'DJF' and j ==1:  # if it's winter we have to go back a year to get december
            #     filepath = pathname_data+'by_month/'+str(years[i]-1)+mos[j]+'.nc'
            # else:
            filepath = pathname_data+'ERA5_1991-2020/era5-T-'+str(years[i])+'-'+mos[j]+'.nc'

            ds = xr.open_dataset(filepath)
            ds1 = xr.concat([ds1,ds],dim='time')

        T = ds1.t2m.resample(time="1D",origin=datetime(1901,1,1,6)).mean()
        #P = ds1.tp.resample(time="1D",origin=datetime(1901,1,1,7)).sum() # 7 hours from utc, since precip is labelled for the previous hour
        
        time_slice = slice(year_start+'-'+mos[0],str(years[i])+'-'+mos[-1])
        T = T.sel(time=time_slice)
        #P = P.sel(time=time_slice)

        regions_file = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
        regions=gp.GeoDataFrame(columns=['set'],geometry=[regions_file.unary_union])

        mask = regionmask.mask_3D_geopandas(regions, T.longitude, T.latitude)
        T = T.where(mask.sel(region=0)).mean() - 273.15  # K to C
        #P = P.where(mask.sel(region=0)).mean(dim=['latitude','longitude']).sum() * 1000  # m to mm

        T= np.round(T.values,2)
        #P= np.round(P.values,2)

        #T_list.append(T)
        #P_list.append(P)

        print(T)

    return None




if __name__ == "__main__":
    pathname = paths['pathname']
    pathname_data = paths['pathname_data']
    
    # years = range(2020,2025)
    # vars = ['T','P']
    # var_xr = ['t2m','tp']
    # months = ['01','02','12']
    # mos = [1,2,12]

    # filepath = pathname_data+'era5-TP-2020-2025.grib'

    # for j in range(len(vars)):
    #     ds1 = cfgrib.open_datasets(filepath)[j]
    #     if vars[j] == 'P':
    #         ds1 = xr.Dataset({"tp":(["time","latitude","longitude"],ds1.tp.values.reshape((len(ds1.time)*len(ds1.step),len(ds1.latitude),len(ds1.longitude))))},
    #             {"time":("time",ds1.valid_time.values.flatten()),"latitude":ds1.latitude,"longitude":ds1.longitude})
    #         ds1 = ds1.dropna(dim='time')
    #     for y in range(len(years)):
    #         ds = ds1.sel(time=ds1.time.dt.year.isin([years[y]]))
    #         for i in range(len(mos)):
    #             ds2 = ds.sel(time=ds.time.dt.month.isin([mos[i]]))
    #             ds2.to_netcdf(pathname_data+'ERA5_1991-2020/era5-'+vars[j]+'-'+str(years[y])+'-'+months[i]+'.nc')


    # for i in range(len(years)):
 
    #     ds1 = xr.open_dataset(files[0])
    #     for j in range(12):
    #         ds = ds1.sel(time=ds1.time.dt.month.isin([mos[j]]))
    #         ds.to_netcdf(pathname_data+'ERA5_1991-2020/era5-T-'+str(years[i])+'-'+months[j]+'.nc')
    lons = vars['lons']
    lats = vars['lats']
    daily_to_monthly()
    