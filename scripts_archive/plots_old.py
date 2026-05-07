from matplotlib import pyplot as plt
import numpy as np
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")
import regionmask
import geopandas as gp
import cfgrib
from datetime import datetime
from shapely.geometry import Polygon, MultiPolygon


def create_colormap():
    colors = [(5/255, 48/255, 110/255), (1, 1, 1), (140/255, 20/255, 0/255)]  # B -> W -> R
    cmap_name = 'temp_RB'
    temp_RB = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    temp_RB.set_over((120/255, 20/255, 0/255))
    temp_RB.set_under((5/255, 48/255, 100/255))

    colors = [(0,(1/255, 56/255, 130/255)), (0.5,(1, 1, 1)), (0.6,(252/255,250/255,150/255)), (0.69,(252/255,215/255,40/255)),
              (0.8,(239/255,133/255,27/255)), (1,(153/255, 0/255, 5/255))]  # B -> W -> Y -> YO -> O -> R
    cmap_name = 'temp_ROYB'
    temp_ROYB = LinearSegmentedColormap.from_list(cmap_name, colors, N=27)
    temp_ROYB.set_over((135/255, 0/255, 5/255))
    temp_ROYB.set_under((1/255, 56/255, 110/255))

    colors = [(0,(1/255, 56/255, 130/255)), (0.25,(80/255,235/255,235/255)), (0.5,(1, 1, 1)), (0.58,(252/255,250/255,150/255)),
              (0.65,(252/255,225/255,50/255)),
              (0.75,(245/255,154/255,10/255)), (0.89,(237/255,43/255,33/255)),(1,(140/255, 0/255, 5/255))]  # B -> C -> W -> Y -> YO -> O -> R
    cmap_name = 'temp_ROYCB'
    temp_ROYCB = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)
    temp_ROYCB.set_over((125/255, 0/255, 5/255))
    temp_ROYCB.set_under((1/255, 56/255, 120/255))

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


def simplify_shp(in_file='data/Inuit_Region_Region_inuite.shp'):
    # from https://stackoverflow.com/questions/78987052/simplify-polygon-shapefile-to-reduce-file-size-in-python

    input_path = in_file
    output_path = r"shapefile_simplified.shp"

    # Read the shapefile
    gdf = gp.read_file(input_path)

    def simplify_geometry(geom, tolerance=0.2):
        if isinstance(geom, Polygon):
            return geom.simplify(tolerance, preserve_topology=True)
        elif isinstance(geom, MultiPolygon):
            return MultiPolygon([polygon.simplify(tolerance, preserve_topology=True) for polygon in geom.geoms])
        return geom
    
    gdf['geometry'] = gdf['geometry'].apply(simplify_geometry)
    gdf.to_file(output_path)

def plot_data_domain(ds):
    proj=ccrs.Stereographic(central_longitude=280,central_latitude=70)
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(1,1,1,projection=proj)

    cs = ax.contourf(ds.longitude,ds.latitude,np.ones([len(ds.latitude),len(ds.longitude)]),transform=ccrs.PlateCarree(),colors='blue',alpha=0.15)
    regions = gp.read_file(pathname_data+'/Inuit_Region_Region_inuite.shp')
    regions.plot(ax=ax,color='blue',alpha=0.5,edgecolor='blue',transform=ccrs.PlateCarree())
    ax.set_aspect('equal')
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_0_boundary_lines_land', scale='50m', facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.7))

    # Create gridlines
    gl = ax.gridlines(linewidth=0.8, color='black', alpha=0.2,linestyle='--',crs=ccrs.PlateCarree(),x_inline=False,y_inline=False)
    # Manipulate gridlines number and spaces
    gl.ylocator = mticker.FixedLocator(np.arange(-90,90,5))
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, 10))
    gl.xlabel_style = {'size': 12,'rotation':40}
    gl.ylabel_style = {'size': 12}
    gl.bottom_labels = True
    gl.left_labels = True

    plt.savefig('plots/domain.png')


def plot_regional_domain(ds):
    proj=ccrs.Stereographic(central_longitude=280,central_latitude=70)
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(1,1,1,projection=proj)

    regions = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
    mask = regionmask.mask_3D_geopandas(regions, ds.longitude, ds.latitude,overlap=True)

    ds1 = ds.where(mask.sel(region=0))
    cs = ax.contourf(ds1.longitude,ds1.latitude,ds1.t2m,transform=ccrs.PlateCarree(),colors='blue',alpha=0.3)
    ds2 = ds.where(mask.sel(region=1))
    cs = ax.contourf(ds2.longitude,ds2.latitude,ds2.t2m,transform=ccrs.PlateCarree(),colors='orange',alpha=0.4)
    ds3 = ds.where(mask.sel(region=2))
    cs = ax.contourf(ds3.longitude,ds3.latitude,ds3.t2m,transform=ccrs.PlateCarree(),colors='red',alpha=0.3)
    ds4 = ds.where(mask.sel(region=3))
    cs = ax.contourf(ds4.longitude,ds4.latitude,ds4.t2m,transform=ccrs.PlateCarree(),colors='green',alpha=0.3)
    
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_0_boundary_lines_land', scale='50m', facecolor='none', edgecolor='k',alpha=0.6,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.6,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.7,linewidth=0.7))

    # Create gridlines
    gl = ax.gridlines(linewidth=0.8, color='black', alpha=0.2,linestyle='--',crs=ccrs.PlateCarree(),x_inline=False,y_inline=False)
    # Manipulate gridlines number and spaces
    gl.ylocator = mticker.FixedLocator(np.arange(-90,90,5))
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, 10))
    gl.xlabel_style = {'size': 12,'rotation':40}
    gl.ylabel_style = {'size': 12}
    gl.bottom_labels = True
    gl.left_labels = True

    plt.savefig('plots/regional_domain.png')


def grib_to_nc(filename):
    ds = cfgrib.open_datasets(filename)
    T = ds[0]
    P = ds[1]

    T = T.sel(time=slice('2024-11-30','2025-03-01'))
    P = P.sel(time=slice('2024-11-30','2025-03-01'))

    # T = T.sel(time=slice('2023-11-30','2024-03-01'))
    # P = P.sel(time=slice('2023-11-30','2024-03-01'))

    P = xr.Dataset({"tp":(["time","latitude","longitude"],P.tp.values.reshape((len(P.time)*len(P.step),len(P.latitude),len(P.longitude))))},
                     {"time":("time",P.valid_time.values.flatten()),"latitude":P.latitude,"longitude":P.longitude})
    P = P.dropna(dim='time')
    P['tp'] = P['tp'] * 1000 # m to mm
    P = P.resample(time="1D",origin=datetime(1991,1,1,7)).sum()

    T = T.resample(time="1D",origin=datetime(1991,1,1,6)).mean()

    P.to_netcdf(pathname_data+'era5-P-'+filename[-13:-5]+'.nc')  # todo: these numbers depend on length of filepath! not transfer friendly
    T.to_netcdf(pathname_data+'era5-T-'+filename[-13:-5]+'.nc')


def plot_monthly_normals(ds,month=12,month_name='December'):
    proj=ccrs.Stereographic(central_longitude=280,central_latitude=70)
    fig = plt.figure(figsize=(12,8))
    ax = plt.subplot(1,1,1,projection=proj)

    cs = ax.contourf(ds.longitude,ds.latitude,ds.groupby('month').mean().sel(month=month).t2m,transform=ccrs.PlateCarree())
    fig.colorbar(cs,label=r"$^\circ$C",fraction=0.1, pad=0.04)
    ax.set_title(month_name+' 1991-2020 Normals')

    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_0_boundary_lines_land', scale='50m', facecolor='none', edgecolor='k',alpha=0.6,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.6,linewidth=0.7))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.7,linewidth=0.7))

    # Create gridlines
    gl = ax.gridlines(linewidth=0.8, color='black', alpha=0.2,linestyle='--',crs=ccrs.PlateCarree(),x_inline=False,y_inline=False)
    # Manipulate gridlines number and spaces
    gl.ylocator = mticker.FixedLocator(np.arange(-90,90,5))
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, 10))
    gl.xlabel_style = {'size': 12,'rotation':40}
    gl.ylabel_style = {'size': 12}
    gl.bottom_labels = True
    gl.left_labels = True

    plt.tight_layout()
    plt.savefig('plots/'+month_name+'-normals2.png')


def calc_anomalies(ds,normals,season='DJF'):
    if season == 'DJF':
        months = [12]#[12,1,2]
    elif season == 'MAM':
        months = [3,4,5]
    elif season == 'JJA':
        months = [6,7,8]
    elif season == 'SON':
        months = [9,10,11]
    else:
        raise ValueError('Need to input season in form DJF, MAM, JJA, SON')

    if var == 'T':
        seas = ds.mean(dim='time')
        normals = normals.groupby('month').mean()
        seas_norm = normals.sel(month=months).mean(dim='month')
        seas_anom = seas - seas_norm

        ds = ds.groupby('time.month').mean()
    elif var == 'P':
        seas = ds.sum(dim='time')
        normals = normals.groupby('month').sum()
        seas_norm = normals.sel(month=months).sum(dim='month')
        seas_anom = (seas / seas_norm)*100

        ds = ds.groupby('time.month').sum()

    month_anoms = []
    for i in range(len(months)):
        if var == 'T':
            m_anom = ds.sel(month=months[i]) - normals.sel(month=months[i])
        elif var == 'P':
            m_anom = (ds.sel(month=months[i]) / normals.sel(month=months[i]))*100
        month_anoms.append(m_anom)

    return seas_anom, month_anoms


def mask_anomalies(ds):
    regions_file = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
    regions=gp.GeoDataFrame(columns=['set'],geometry=[regions_file.unary_union])

    mask = regionmask.mask_3D_geopandas(regions, ds.longitude, ds.latitude)
    ds = ds.where(mask.sel(region=0))

    if var == 'T':
        return np.round(ds.t2m.mean(),2)
    else:
        return np.round(ds.tp.mean(),0)

def plot_anomalies(ds,plt_title = 'DJF'):
    proj=ccrs.Stereographic(central_longitude=262,central_latitude=70)
    fig = plt.figure(figsize=(12,8))
    ax = plt.subplot(1,1,1,projection=proj)

    ax.set_facecolor('lightgrey')

    # plotting region boundaries
    regions.boundary.plot(ax=ax,color='k',transform=ccrs.PlateCarree(),linewidth=0.6)
    ax.set_aspect('equal')
    l_width_bottom = 1.7
    ax.plot(np.linspace(-63.5,-78.5,100),np.repeat([55],100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # quebec
    ax.plot(np.linspace(-94.8,-102,100),np.repeat([60],100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # bottom of NU
    ax.plot(np.repeat([-102],100),np.linspace(60,64.2,100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # side of NU
    ax.plot(np.linspace(-102,-109.2,100),np.linspace(64.2,64.85,100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # bottom of NU
    ax.plot(np.linspace(-109.2,-110.9,100),np.linspace(64.85,65.5,100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # bottom of NU
    ax.plot(np.linspace(-110.9,-112.5,100),np.linspace(65.5,65.5,100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # bottom of NU
    ax.plot(np.linspace(-112.5,-120.7,100),np.linspace(65.5,68,100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # bottom of NU
    ax.plot(np.linspace(-120.7,-132,100),np.repeat([68],100),color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # top of NWT
    ax.plot([-132,-132,-133.6,-133.6,-136.2],[68,68.5,68.5,68.2,68.2],color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # top of NWT
    ax.plot([-136.2,-136.4,-137,-138,-138,-140.9],[68.2,67.6,68.2,68.2,68.5,68.6],color='k',transform=ccrs.PlateCarree(),linewidth=l_width_bottom) # YT

    # plotting data
    data = ds.to_dataarray()[0,:,:]
    if var == 'P':
        vmin = 0
        vmax = P_max
        extend = 'max'
        #data=np.where((75 <= data) & (data <= 125),100,data)
    else:
        # vmin = np.floor(data.min())
        # vmax=np.ceil(data.max())
        vmin = T_min
        vmax = T_max
        extend = 'both'
        #data=np.where((-1 <= data) & (data <= 1),0,data)
    divnorm = mpl.colors.TwoSlopeNorm(vmin=vmin, vcenter=centre_value, vmax=vmax)

    cs = ax.contourf(ds.longitude,ds.latitude,data,transform=ccrs.PlateCarree(),
                     cmap=cmap,norm=divnorm,levels=cbar_levels,extend=extend)
    if plt_title == 'DJF':
        cbar = fig.colorbar(cs,orientation='horizontal',shrink=0.7,pad=0.03)
    else:
        cbar = fig.colorbar(cs,orientation='vertical',shrink=0.8,pad=0.02)
    cbar.ax.tick_params(labelsize=13)
    cbar.set_ticks(cbar_levels)
    if var == 'T':
        cbar.set_label(label=r"Temperature anomaly ($^\circ$C )",fontsize=17)
    else:
        cbar.set_label(label=r"Precip as % of normal",fontsize=17)
    ax.set_title(plt_title,fontsize=32)

    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_0_boundary_lines_land', scale='50m', facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))

    # Create gridlines
    gl = ax.gridlines(linewidth=0.8, color='black', alpha=0.2,linestyle='--',
                      crs=ccrs.PlateCarree(),x_inline=False,y_inline=False)
    # Manipulate gridlines number and spaces
    gl.ylocator = mticker.FixedLocator(np.arange(-90,90,5))
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 0, 10))
    gl.xlabel_style = {'size': 14,'rotation':40}
    gl.ylabel_style = {'size': 14,'rotation':-30}

    # total domain boundary lines
    gl2 = ax.gridlines(linewidth=0.8, color='black',crs=ccrs.PlateCarree())
    gl2.ylocator = mticker.FixedLocator([53,84])
    gl2.xlocator = mticker.FixedLocator([-55,-142])

    # plot locations
    y_coords, x_coords = zip(*places)
    label_y, label_x = zip(*place_name_locations)
    ax.scatter(x_coords,y_coords,c='k',marker='o',transform=ccrs.PlateCarree())
    for i, txt in enumerate(place_names):
        ax.annotate(txt,(label_x[i],label_y[i]),transform=ccrs.PlateCarree(),fontsize=8.5,fontweight='bold')
    plt.tight_layout()
    plt.savefig(pathname+'plots/test-2024-'+plt_title+'-'+var+'-anomalies.png')


if __name__ == "__main__":
    pathname = "/home/psotkaj/era5_for_arcc/"
    pathname_data = '/home/psotkaj/clim4/era5-data/'
    var = 'P'
    regions = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
    places = [(63.748651, -68.515855),(62.809285, -92.086992),(76.424718, -82.889151),(69.121958, -105.058614)] 
    place_names = ['Iqaluit','Rankin Inlet','Grise Fiord','Cambridge Bay']
    place_name_locations = [(64.5, -70.3),(62.15, -91.8),(76.9, -87),(69, -113.5)]  # coords of labels

    norm = xr.open_dataset(pathname_data+'normals-1991-2020.nc')#xr.open_dataset(pathname_data+'era5-'+var+'-normals.nc')
    #szn = xr.open_dataset(pathname_data+'era5-'+var+'-2025-DJF.nc')
    szn = xr.open_dataset(pathname_data+'monthly/2024-12.nc')
    szn = szn.sel(longitude=slice(-145,-55),latitude=slice(84,53))
    norm = norm.sel(longitude=slice(-145,-55),latitude=slice(84,53))

    if var == 'T':
        norm['t2m'] -= 273.15
        szn['t2m'] -= 273.15

    #plot_data_domain(norm.isel(month_day=1))
    #plot_monthly_normals(norm,2,'February')

    seas_anom,month_anoms = calc_anomalies(szn,norm,'DJF')
    month_anoms.append(seas_anom)
    mos = ['December','January','Feburary','DJF'] # ['June','July','Aug','JJA']  # this order matters! should change this to be auto instead of manual lists
    for i in range(len(mos)):
        if var == 'T':
            print(mos[i]+" total T anomaly for the region: ",mask_anomalies(month_anoms[i]).values,"deg C")
            # T_min = np.floor(np.min(month_anoms[i].t2m.values))
            # T_max = np.ceil(np.max(month_anoms[i].t2m.values))
            T_min = -5
            T_max = 11
            cbar_levels = np.arange(T_min,T_max+1,1)
            cbar_levels = np.delete(cbar_levels,np.where(cbar_levels==0))
            #cbar_levels = [-5,-3,-1,1,3,5,7,9,11]
            cmap = create_colormap()['temp_ROYCB']
            centre_value = 0
            
        elif var == 'P':
            print(mos[i]+" total P anomaly for the region: ",mask_anomalies(month_anoms[i]).values,"%")
            cmap = create_colormap()['precip_BrGBg']
            #P_max = np.ceil(np.max(month_anoms[i].tp.values))
            P_max = 300
            cbar_levels = [0,25,50,75,90,110,125,150,175,200,250,300]#[0,15,30,45,60,75,90,110,125,140,155,170,185,200,225,250,275,300]
            centre_value = 100

        plot_anomalies(month_anoms[i],mos[i])