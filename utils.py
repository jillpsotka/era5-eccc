import numpy as np
import xarray as xr
import glob
from datetime import datetime
from setup import paths, vars
from matplotlib.colors import LinearSegmentedColormap


def daily_to_monthly(year, month, incomplete=False):
    # merge daily data files into monthly
    filepath_next_month = paths['pathname_data']+'daily/era5-'+year+'-'+datetime.strftime(datetime.today(),'%m')+'-01.nc'
    if month == '12': # december
        year = str(int(year)-1)

    filepath = paths['pathname_data']+'daily/era5-'+year+'-'+month+'*.nc'
    files = glob.glob(filepath)
    files.sort()
    # now add in the first day of the next month, so we can resample hourly -> daily from 06Z-06Z

    if not incomplete:
        files.append(filepath_next_month)
    ds1 = xr.open_dataset(files[0])
    for f in files[1:]:
        ds = xr.open_dataset(f)
        ds1 = xr.concat([ds1,ds],dim='time')

    T = ds1.t2m.resample(time="1D",origin=datetime(1901,1,1,6)).mean()  # resample hourly -> daily from 06Z-06Z
    P = ds1.tp.resample(time="1D",origin=datetime(1901,1,1,7)).sum()  # resample hourly -> daily from 06Z-06Z
    # we want P from 07Z-07Z so that when we take 1 climatological day (06Z-06Z), P represents total precip that fell on that day
    P['time'] = P.time-int(1*60*60*1E9) # shift time axis to match T
    ds1 = xr.merge([T,P])
    ds1 = ds1.sel(time=ds1.time.dt.month.isin([int(month)]))
    ds1.to_netcdf(paths['pathname_data']+'monthly/'+year+'-'+month+'.nc')


def create_colormap():  # create custom colour maps
    colors = [(5/255, 48/255, 110/255), (1, 1, 1), (140/255, 20/255, 0/255)]  # B -> W -> R
    cmap_name = 'temp_RB'
    temp_RB = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    temp_RB.set_over((120/255, 20/255, 0/255))
    temp_RB.set_under((5/255, 48/255, 100/255))

    # here the first argument of each element is the relative location on the colour bar (from 0-1)
    # for example (0.5,(1, 1, 1)) makes it so that white is at the middle value
    colors = [(0,(1/255, 56/255, 130/255)), (0.5,(1, 1, 1)), (0.6,(252/255,250/255,150/255)), (0.69,(252/255,215/255,40/255)),
              (0.8,(239/255,133/255,27/255)), (1,(153/255, 0/255, 5/255))]  # B -> W -> Y -> YO -> O -> R
    cmap_name = 'temp_ROYB'
    temp_ROYB = LinearSegmentedColormap.from_list(cmap_name, colors, N=27)
    temp_ROYB.set_over((135/255, 0/255, 5/255))
    temp_ROYB.set_under((1/255, 56/255, 110/255))

    colors = [(0,(76/255, 0/255, 115/255)), (0.05,(85/255,40/255,180/255)), (0.15,(60/255,90/255,180/255)),(0.34,(80/255,235/255,235/255)),
              (0.39,(200/255,240/255,240/255)),(0.5,(1, 1, 1)), (0.58,(252/255,250/255,150/255)),(0.65,(252/255,225/255,50/255)),
              (0.75,(245/255,154/255,10/255)), (0.89,(237/255,43/255,33/255)),(1,(140/255, 0/255, 5/255))]  # P -> B -> C -> W -> Y -> YO -> O -> R
    cmap_name = 'temp_ROYCB'
    temp_ROYCB = LinearSegmentedColormap.from_list(cmap_name, colors, N=256)
    temp_ROYCB.set_over((125/255, 0/255, 5/255))
    temp_ROYCB.set_under((65/255, 0/255, 96/255))

    colors = [(0,(80/255, 35/255, 0/255)), (0.25,(207/255,151/255,107/255)), (0.5,(1, 1, 1)),  (0.6,(183/255, 240/255, 173/255)), (0.7,(25/255, 130/255, 60/255)),
              (1,(20/255,20/255,130/255))]  # Br -> W -> G -> B
    cmap_name = 'precip_BrGB'
    precip_BBB = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    precip_BBB.set_over((80/255, 10/255, 110/255))

    colors = [(0,(80/255, 35/255, 0/255)), (0.25,(207/255,151/255,107/255)), (0.5,(1, 1, 1)), (0.7,(25/255, 130/255, 25/255)),
              (0.85,(27/255,39/255,168/255)),(1,(76/255,21/255,100/255))]  # Br -> W -> G -> B -> P
    cmap_name = 'precip_BB'
    precip_BB = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    precip_BB.set_over((80/255, 10/255, 110/255))

    colors = [(0,(120/255, 60/255, 0/255)), (0.5,(1, 1, 1)), (0.7,(94/255,219/255,202/255)), (1,(0/255,90/255,90/255))]  # Br -> W -> Bg
    cmap_name = 'precip_BrBg'
    precip_BrBg = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    precip_BrBg.set_over((0/255, 70/255, 70/255))

    colors = [(0,(100/255, 60/255, 10/255)), (0.25,(207/255,151/255,107/255)),(0.5,(1, 1, 1)), #(0.4,(245/255,230/255,170/255))
              (0.65,(83/255, 170/255, 61/255)),(0.73,(94/255,210/255,220/255)), (1,(0/255,90/255,100/255))]  # Br -> W -> G -> Bg
    cmap_name = 'precip_BrGBg'
    precip_BrGBg = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    precip_BrGBg.set_over((0/255, 85/255, 95/255))

    cmap_dict = {'temp_RB':temp_RB,'temp_ROYB':temp_ROYB, 'temp_ROYCB':temp_ROYCB, 'precip_BrGB':precip_BBB,
                 'precip_BB':precip_BB,'precip_BrBg':precip_BrBg,'precip_BrGBg':precip_BrGBg}
    return cmap_dict