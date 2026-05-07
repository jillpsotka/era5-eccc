from zipfile import ZipFile as zip
import pandas as pd
import geopandas as gp
from shapely.geometry import Point
import xarray as xr
import glob
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
from datetime import datetime, timedelta


def get_ahccd(file, stationfile):
    stations = pd.read_csv(stationfile)  # file with station metadata
    stations.rename(columns={'lat (deg)': 'lat', 'long (deg)': 'lon'}, inplace=True)
    stations["inuit_region"] = ""
    regions_file = gp.read_file('/home/psotkaj/clim4/era5-data/Inuit_Region_Region_inuite.shp')  # file with inuit regions
    regions=gp.GeoDataFrame(columns=['set'],geometry=[regions_file.union_all()])

    for i in stations.index:
        boo = regions.geometry[0].contains(Point(stations.lon.values[i],stations.lat.values[i]))
        stations.loc[i,"inuit_region"] = boo
        stations.loc[i,"stnid"] = stations.loc[i,"stnid"].strip()
    inuit_stations = stations.loc[stations['inuit_region']]
    inuit_stations.set_index("station's name",inplace=True)

    data = {}
    with zip(file, 'r') as z:
        for stnid in inuit_stations['stnid'].values:
            filename = f"mt{stnid}.txt"
            if filename in z.namelist():  # Check if file exists in zip
                with z.open(filename) as f:
                    df = pd.read_csv(f, delimiter=",",encoding="latin-1",skiprows=3,index_col=False)
                    df = df.drop(df.columns[range(2,34,2)],axis=1) # drop random empty columns in the data
                    df.columns = df.columns.str.strip()
                    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

                    if "Avr" not in df.columns:
                        print('Problem with data reading/parsing')
                        raise ValueError("something went wrong with reading station csv file")
                    data[stnid] = df
            else:
                print(f"File {filename} not found in zip.")

    return data, inuit_stations


def get_era5(stations):
    # have to open each era5 file for each day and pull out the grid points we are interested in
    data_files = glob.glob('/home/psotkaj/clim4/era5-data/monthly/*.nc')
    xr_list = []
    for f in data_files:
        mth = xr.open_dataset(f)
        mth = mth.sel(latitude=stations['lat'].values,longitude=stations['lon'].values,method='nearest')
        xr_list.append(mth)
    era5_data = xr.concat(xr_list,dim='time')
    era5_data.to_netcdf('/home/psotkaj/clim4/era5-data/stations_dly.nc')

    return era5_data


def single_plots(st,st_meta,era5,month=range(1,13)):
    era5 = era5.sel(time=era5.time.dt.month.isin([month]))
    era_point = era5.sortby('latitude').sel(latitude=st_meta['lat'],method="nearest")
    era_point = era_point.sortby('longitude').sel(longitude=st_meta['lon'],method="nearest")
    eraP = era_point.tp.resample(time="1MS").sum()

    st.replace(-9999.9, np.nan, inplace=True)
    months = ['Janv', 'Fév', 'Mars', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
    df_monthly = st[['An'] + months]
    df_long = df_monthly.melt(id_vars='An', var_name='month', value_name='value')
    month_map = {
        'Janv': 1, 'Fév': 2, 'Mars': 3, 'Avr': 4, 'Mai': 5, 'Juin': 6,
        'Juil': 7, 'Août': 8, 'Sept': 9, 'Oct': 10, 'Nov': 11, 'Déc': 12
    }
    df_long['month_num'] = df_long['month'].map(month_map)
    # Create time coordinate (first day of each month)
    df_long['time'] = pd.to_datetime(dict(year=df_long['An'], month=df_long['month_num'], day=1))

    da = xr.DataArray(np.array(df_long['value'].values,dtype=float),coords={'time': df_long['time'].values},dims=['time']).sortby('time')
    da = da.dropna('time').sel(time=slice("1980",None))
    da = da.sel(time=da.time.dt.month.isin([month]))
    time_axis = da.time

    # Compute normals and anomalies for ERA5
    P_normals_era = eraP.sel(time=slice('1981-01-01','2010-12-01')).groupby('time.month').mean()
    P_std_era = eraP.sel(time=slice('1981-01-01','2010-12-01')).groupby('time.month').std()
    era_anom = ((eraP.groupby('time.month') / P_normals_era) * 100).sel(time=time_axis)
    #era_anom = eraP.sel(time=time_axis)
    #era_values = eraP.sel(time=slice('2010-01-01','2018-01-01'))

    # Compute normals and anomalies for observations
    P_normals_obs = da.sel(time=slice('1981-01-01','2010-12-01')).groupby('time.month').mean()
    P_std_obs = da.sel(time=slice('1981-01-01','2010-12-01')).groupby('time.month').std()
    obs_anom = ((da.groupby('time.month') / P_normals_obs) * 100)
    #obs_values = da.sel(time=slice('2010-01-01','2018-01-01'))

    # Difference between anomalies
    diff = era_anom - obs_anom
    colors = ['green' if val > 0 else 'brown' for val in diff]

    # Create figure and subplots
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10))

    # First subplot: normals
    if month == [12,1,2]:
        axes[0].plot([0,1,2], P_normals_era.sel(month=month).values, label='ERA5 Normals', marker='o', color='red')
        axes[0].fill_between([0,1,2], (P_normals_era.sel(month=month).values + P_std_era.sel(month=month).values), (P_normals_era.sel(month=month).values - P_std_era.sel(month=month).values), alpha=0.1, color='red', label='+/- 1 SD')
        axes[0].plot([0,1,2], P_normals_obs.sel(month=month).values, label='AHCCD Normals', marker='s',color='blue')
        axes[0].fill_between([0,1,2], (P_normals_obs.sel(month=month).values + P_std_obs.sel(month=month).values), (P_normals_obs.sel(month=month).values - P_std_obs.sel(month=month).values), alpha=0.1, color='blue', label='+/- 1 SD')
        axes[0].set_xticks([0,1,2],['12','1','2'])
    else:
        axes[0].plot(P_normals_era.month, P_normals_era.values, label='ERA5 Normals', marker='o', color='red')
        axes[0].fill_between(P_normals_era.month, (P_normals_era + P_std_era), (P_normals_era - P_std_era), alpha=0.1, color='red', label='+/- 1 SD')
        axes[0].plot(P_normals_obs.month, P_normals_obs.values, label='AHCCD Normals', marker='s',color='blue')
        axes[0].fill_between(P_normals_obs.month, (P_normals_obs + P_std_obs), (P_normals_obs - P_std_obs), alpha=0.1, color='blue', label='+/- 1 SD')
        axes[0].set_xticks(month)

    axes[0].set_title('Monthly Precipitation Normals (1981-2010)')
    axes[0].set_ylabel('Precip (mm)')
    axes[0].set_xlabel('Month')
    axes[0].legend()
    axes[0].grid(True)


    # Second subplot: anomaly difference
    # RMSE
    rmse = np.sqrt(np.mean((era_anom - obs_anom)**2))
    rmse_list.append(float(rmse))
    bias = np.mean(era_anom - obs_anom)
    bias_list.append(float(bias))
    mae = np.mean(np.abs(era_anom - obs_anom))
    mae_list.append(float(mae))
    # R2
    regr = linregress(obs_anom,era_anom)
    R2= regr.rvalue**2
    pvalue= regr.pvalue
    slope= regr.slope
    intercept =regr.intercept
    # geometric mean slope
    regr2 = linregress(era_anom,obs_anom)
    geo_slope=np.mean([regr2.slope,regr.slope])
    geo_slope_list.append(float(geo_slope))

    axes[2].bar(diff.time.values, diff.values, label='ERA5 - AHCCD Anomaly Difference', color=colors,width=np.timedelta64(21, 'D'))
    axes[2].axhline(0, color='black', linewidth=1)
    axes[2].set_title(f"Difference of Monthly Precip as % of normal (ERA5 - AHCCD)\n MAE={mae:.0f}%   bias={bias:.0f}%   RMSE={rmse:.0f}%   geometric mean slope={geo_slope:.2f}")
    axes[2].set_ylabel('Difference (%)')
    axes[2].grid(True)

    # # third subplot: percent of normal, time series
    # axes[2].plot(era_values.time.values, era_values.values, label='ERA5 precip mm', marker='o', color='red')
    # #axes[2].fill_between(P_normals_era.month, (P_normals_era + P_std_era), (P_normals_era - P_std_era), alpha=0.1, color='red', label='+/- 1 SD')
    # axes[2].plot(obs_values.time.values, obs_values.values, label='AHCCD precip mm', marker='s',color='blue')
    # #axes[2].fill_between(P_normals_obs.month, (P_normals_obs + P_std_obs), (P_normals_obs - P_std_obs), alpha=0.1, color='blue', label='+/- 1 SD')
    # axes[2].set_title(f"Monthly Precipitation mm")
    # axes[2].set_ylabel('Precip (mm)')
    # axes[2].legend()
    # axes[2].grid(True)

    # third subplot: percent of normal, time series
    axes[1].plot(time_axis.isel(time=slice(-1*(10*len(month)),-1)), era_anom.isel(time=slice(-1*(10*len(month)),-1)).values, lw=1,label='ERA5 precip %', marker='o', color='red')
    axes[1].plot(time_axis.isel(time=slice(-1*(10*len(month)),-1)), obs_anom.isel(time=slice(-1*(10*len(month)),-1)).values, lw=1,label='AHCCD precip %', marker='s',color='blue')
    axes[1].set_title(f"Monthly Precipitation % of normal for the last 10 years of AHCCD data for this station")
    axes[1].set_ylabel('Precip (%)')
    axes[1].legend()
    axes[1].grid(True)

    fig.suptitle(f'Precipitation Analysis: {st_meta.name}', fontsize=14)
    print(st_meta.name)
    fig.tight_layout()
    fig.savefig('case-studies/plots-year-since-1980/'+st_meta.name+'-year.png')

    return None


if __name__ == "__main__":
    data, metadata = get_ahccd("case-studies/Adj_monthly_total_prec.zip","case-studies/Precipitation_Stations.csv")
    # data is a dictionary of time series data where keys are stn ids
    # stn ids for inuit stations are found in metadata pandas df

    #get_era5(metadata) only have to do once per set of stations
    era5 = xr.open_dataset('/home/psotkaj/clim4/era5-data/inuit_stations_dly.nc')
    era5 = era5.drop_duplicates(['latitude','longitude']).sortby('time')

    # metadata[metadata['end yr']>2009]
    mae_list = []
    rmse_list = []
    bias_list = []
    geo_slope_list = []
    for stn in metadata[metadata['end yr']>2009].index:
        single_plots(data[metadata.loc[stn]['stnid']],metadata.loc[stn],era5)#,[12,1,2])

    print(mae_list)
    print(rmse_list)
    print(bias_list)
    print(geo_slope_list)