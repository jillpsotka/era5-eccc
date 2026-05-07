import xarray as xr
import sys
import os
import glob


def chop(file):
    ds = xr.open_dataset(file)
    ds = ds.drop_vars('fg10')

    ds['tp'] = ds['tp'] * 1000 # m to mm
    ds = ds.dropna(dim='time')

    ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
    ds = ds.sortby(ds.longitude)
    ds = ds.sel(longitude=lons,latitude=lats)

    start = str(ds.time.values[0])[:10]
    if len(ds.longitude) != 0:
        ds.to_netcdf(pathname_data+"daily/era5-"+start+".nc")
        os.remove(file)

    return None


def daily_to_monthly():
    # merge daily files into monthly
    years = range(2024,2025)
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    for i in range(len(years)):
        for j in range(len(months)):
            filepath = pathname_data+'from_ruping/'+str(years[i])+months[j]+'/*.nc'
            files = glob.glob(filepath)
            files.sort()

            #ds1 = xr.open_dataset(files[0]).drop_vars(['fg10'])
            ds1.coords['longitude'] = (ds1.coords['longitude'] + 180) % 360 - 180
            ds1 = ds1.sortby(ds1.longitude)
            ds1 = ds1.sel(longitude=lons,latitude=lats)
            for f in files[1:]:
                ds = xr.open_dataset(f).drop_vars(['fg10'])
                ds.coords['longitude'] = (ds.coords['longitude'] + 180) % 360 - 180
                ds = ds.sortby(ds.longitude)
                ds = ds.sel(longitude=lons,latitude=lats)
                ds1 = xr.concat([ds1,ds],dim='time')
            ds1.to_netcdf(pathname_data+'by_month/'+str(years[i])+months[j]+'.nc')
        print('done',years[i])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Need filename as argument")
        sys.exit(1)
    filename = sys.argv[1]

    if not os.path.exists(filename):
        print("File ",filename," not found")
        sys.exit(1)

    lons = slice(-170,-52)
    lats = slice(85,41)
    pathname = "/home/psotkaj/era5_for_arcc/"
    pathname_data = '/home/psotkaj/clim4/era5-data/'
    
    chop(filename)