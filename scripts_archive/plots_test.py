from matplotlib import pyplot as plt
import numpy as np
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import zoom
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.image as mpimg
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
import regionmask
import geopandas as gp
from datetime import datetime, date, timedelta
from setup import paths, vars
import glob
import sys
import utils
from osgeo import gdal, osr
import shutil
import subprocess


def create_colormap():  # maybe move to a utils file?
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


def warp_for_web(ds,var):
    if res == 'month':
        orig_fn = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'.tif'
        output_fn = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'.tif'
        output_final = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'-final.tif'
    else:
        orig_fn = 'tif_plots/'+str(current_year)+'-Jun-Aug-'+var+'.tif'
        output_fn = 'tif_plots/'+str(current_year)+'-Jun-Aug-'+var+'.tif'
        output_final = 'tif_plots/'+str(current_year)+'-JJA-'+var+'-final.tif'
    # Create a copy of the original file and save it as the output filename:
    shutil.copy(orig_fn, output_fn)
    # Open the output file for writing for writing:
    ds = gdal.Open(output_fn, gdal.GA_Update)
    # Set spatial reference:
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326) #4326 is lat/lon

    # Enter the GCPs
    #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
    #   [image column index(x)], [image row index (y)]
    gcps =  [gdal.GCP(-140,65,0,112,777), gdal.GCP(-140,75,0,112,518),
            gdal.GCP(-130,60, 0,198,871), gdal.GCP(-100,65,0,458,777), 
            gdal.GCP(-90,75,0,545,518),    gdal.GCP(-80,55,0,631,952),  
            gdal.GCP(-70,80,0,718,315),    gdal.GCP(-142,75,0,94,518),
            gdal.GCP(-100,83,0,458,138),   gdal.GCP(-65,83,0,761,138), 
            gdal.GCP(-100,80,0,458,315),  gdal.GCP(-60,55,0,804,952),  
            gdal.GCP(-60,60,0,804,871),    gdal.GCP(-70,55,0,718,952), 
            gdal.GCP(-100,54,0,458,966),
            gdal.GCP(-140,84,0,112,61),  gdal.GCP(-130,84,0,198,61),
            gdal.GCP(-120,84,0,285,61),   gdal.GCP(-110,84,0,371,61),
             gdal.GCP(-100,84,0,458,61), gdal.GCP(-140,53,0,112,981),
             gdal.GCP(-90,84,0,545,61),  gdal.GCP(-80,84,0,631,61),
             gdal.GCP(-70,84,0,718,61),     gdal.GCP(-60,84,0,804,61),
             gdal.GCP(-140,55,0,112,952),    gdal.GCP(-60,55,0,804,952),
             gdal.GCP(-140,60,0,112,871),    gdal.GCP(-60,60,0,804,871),
             gdal.GCP(-140,65,0,112,777),    gdal.GCP(-60,65,0,804,777),
             gdal.GCP(-140,80,0,112,315),   gdal.GCP(-130,80,0,198,315),
             gdal.GCP(-120,80,0,285,315),     gdal.GCP(-110,80,0,371,315),
             gdal.GCP(-100,80,0,458,315),    gdal.GCP(-100,55,0,458,952),
             gdal.GCP(-90,80,0,545,315),     gdal.GCP(-80,80,0,631,315),
             gdal.GCP(-60,80,0,804,315),    gdal.GCP(-140,70,0,112,663),
             gdal.GCP(-60,70,0,804,663),    gdal.GCP(-140,80,0,112,315),
             gdal.GCP(-60,80,0,804,315),   gdal.GCP(-142,53,0,94,981),
             gdal.GCP(-142,84,0,94,61),   gdal.GCP(-55,53,0,848,981),
             gdal.GCP(-110,53,0,371,981),   gdal.GCP(-100,53,0,458,981),
             gdal.GCP(-70,53,0,718,981),   gdal.GCP(-60,53,0,804,981),
             gdal.GCP(-55,84,0,848,61),   gdal.GCP(-55,80,0,848,315),
             gdal.GCP(-55,75,0,848,518),   gdal.GCP(-55,70,0,848,663),
             gdal.GCP(-55,60,0,848,871),    gdal.GCP(-60,75,0,804,518)
    ]
    # Apply the GCPs to the open output file:
    ds.SetGCPs(gcps, sr.ExportToWkt())
    # Close the output file in order to be able to work with it in other programs:
    ds = None

    # Part 2: Reproject image from EPSG4326 to EPSG3857
    # ====================================================
    # command for warping to EPSG 3857
    command = [
        'gdalwarp',          # The command to run
        '-s_srs','EPSG:4326', # source CRS is lat/lon'
        '-t_srs', 'EPSG:3857', # Target CRS is Web Mercator
        '-tps',
        '-te','-150','52','-44','84.05',
        '-te_srs','EPSG:4326',
        '-r', 'cubicspline',
        '-overwrite',        # Overwrite the output file if it exists
        output_fn,            # Path to the source dataset
        output_final             # Path to the destination dataset
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    subprocess.run(['cp', '-r', '/home/psotkaj/era5_for_arcc/tif_plots/.', '/home/psotkaj/shiny-server/Project-Climate-Bulletin-ERA5/figs/'])



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


def calc_seasonal_anomalies(ds,normals):

    T = ds.t2m.mean(dim='time')
    T_normals = normals.t2m.groupby('month').mean()
    T_seas_norm = T_normals.mean(dim='month')
    T_anom = T - T_seas_norm

    P = ds.tp.sum(dim='time')
    P_normals = normals.tp.groupby('month').sum()
    P_seas_norm = P_normals.sum(dim='month')
    P_anom = (P / P_seas_norm)*100

    return T_anom, P_anom


def mask_anomalies(ds,var='T'):
    # apply mask for Inuit region to get averages for T and P
    regions_file = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
    regions=gp.GeoDataFrame(columns=['set'],geometry=[regions_file.union_all()])

    mask = regionmask.mask_3D_geopandas(regions, ds.longitude, ds.latitude)
    ds = ds.where(mask.sel(region=0))

    if var == 'T':
        return np.round(ds.mean(),2)
    else:
        return np.round(ds.mean(),0)

def plot_anomalies_tif(ds,var='T'):
    proj=ccrs.epsg(3857)
    fig = plt.figure(figsize=(10,10))
    fig.subplots_adjust(left=0.02, right=0.92, top=0.94, bottom=0.02)
    if res == 'season':
        titles_en = ['Dec-Feb','Mar-May','Jun-Aug','Sep-Nov']
        titles_fr = ['déc-févr','mars-mai','juin-août','sept-nov']
    else:
        titles_en = ['January','February','March','April','May','June','July','August','September','October','November','December']
        titles_fr =['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']
    
    ax = plt.subplot(1,1,1,projection=proj)
    ax.set_facecolor('lightgrey')

    # plotting region boundaries
    if region == 'ARCC':
        regions.boundary.plot(ax=ax,color='k',transform=ccrs.PlateCarree(),linewidth=0.4)
        ax.set_aspect('equal')
        l_width_bottom = 1.7
        # I know this is gross but i needed to plot the bottom boundary thicker without making the islands etc look messy
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
    if var =='P':
        vmin = 0
        vmax = 300
        extend = 'max'
        centre_value = 100
        cbar_levels = [0,25,50,75,90,110,125,150,175,200,250,300]
        cmap = create_colormap()['precip_BrGBg']
        plt_title = 'Precipitation as a Percentage of Normal:  '+str(current_year)+' '+titles_en[last_season_index]+\
                '\nPrécipitation en pourcentage de la normale:  '+str(current_year)+' '+titles_fr[last_season_index]
    else:
        vmin = -10
        vmax = 10
        extend = 'both'
        centre_value = 0
        cbar_levels = np.arange(vmin,vmax+1,1)
        cbar_levels = np.delete(cbar_levels,np.where(cbar_levels==0))
        cmap = create_colormap()['temp_ROYCB']
        plt_title = 'Temperature Anomaly:  '+str(current_year)+' '+titles_en[last_season_index]+\
            '\nAnomalie de température:  '+str(current_year)+' '+titles_fr[last_season_index]

    divnorm = mpl.colors.TwoSlopeNorm(vcenter=centre_value, vmax=vmax, vmin=vmin)
    cs = ax.contourf(ds.longitude,ds.latitude,ds,transform=ccrs.PlateCarree(),
                     cmap=cmap,norm=divnorm,levels=cbar_levels,extend=extend)
    
    #colour bar, titles, logo
    cax = inset_axes(ax, width="3%", height="92%", loc='right', borderpad=-3)
    cbar = fig.colorbar(cs, cax=cax, orientation='vertical')

    cbar.ax.tick_params(labelsize=13)
    cbar.set_ticks(cbar_levels)
    if var == 'T':
        cbar.ax.set_title(label=r"$^\circ$C",fontsize=16,pad=10)
    else:
        cbar.ax.set_title(label=r"%",fontsize=16,pad=10)
    ax.set_title(plt_title,fontsize=22,loc='left')
    fig.text(0.02,0.02,'Source: ERA5. Norm: 1991-2020',fontsize=15)

    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'rivers_lake_centerlines', \
        '110m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'lakes', \
        '110m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))
    logo = mpimg.imread(pathname_data+'eccc_logo.png')
    logo_resized = zoom(logo,(0.4,0.4,1))
    bbox_subp = ax.get_window_extent()
    fig.figimage(logo_resized, xo=fig.bbox.xmax-logo_resized.shape[1]-10, yo=bbox_subp.y0-logo_resized.shape[0]-8, zorder=10)
    if incomplete:
        fig.text(0.9,0.97,'to date ' + (datetime.today()-timedelta(days=5)).strftime("%m-%d"),fontsize=11) 

    # total domain boundary lines
    gl2 = ax.gridlines(linewidth=0.8, color='black',crs=ccrs.PlateCarree())
    gl2.ylocator = mticker.FixedLocator([lats.stop,lats.start])
    gl2.xlocator = mticker.FixedLocator([lons.stop,lons.start])

    # plot locations
    y_coords, x_coords = zip(*places)
    label_y, label_x = zip(*place_name_locations)
    ax.scatter(x_coords,y_coords,c='k',marker='o',transform=ccrs.PlateCarree())
    for i, txt in enumerate(place_names):
        ax.annotate(txt,(label_x[i],label_y[i]),transform=ccrs.PlateCarree(),fontsize=8.5,fontweight='bold')

    if res == 'season':
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+'-anom.png')
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+'-anom.tif')

    else:
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'-anom.png')
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'-anom.tif')
    warp_for_web(ds,var)


if __name__ == "__main__":
    pathname = paths['pathname']
    pathname_data = paths['pathname_data']
    if len(sys.argv) < 3:
        print("Need type of plots (day, month, season) and region (ARCC, PYR, Prairies) as arguments")
        sys.exit(1)
    res = sys.argv[1]  # day or month or season
    region = sys.argv[2] # ARCC, PYR, Prairies
    normal_years = vars['normals_years']
    lons = vars['lons'][region]
    lats = vars['lats'][region]
    incomplete = False
    if len(sys.argv) > 3:  # this allows us to manually set the year and month if we are re-running
        current_year = int(sys.argv[3])
        current_month = int(sys.argv[4])+1
        if len(sys.argv) > 5:
            incomplete = sys.argv[5]  # make the last argument True if you're doing a month-to-date
    else:
        current_year = date.today().year
        current_month = date.today().month

    if res == 'season':
        season_names = ['DJF','MAM','JJA','SON']
        months = [[12, 1, 2],[3, 4, 5],[6, 7, 8],[9, 10, 11]]

        last_season_index = (current_month%12 // 3)-1 # formula maps DJF to 0, MAM to 1, etc, and then -1 to get last season
        last_season = season_names[last_season_index]

        # seasons and their corresponding months/years so that we can pull the relevant files
        # will run this script after season finishes (early March, June, Sept, Dec)
        season_month_indices = {
            'DJF': [str(current_year-1)+'-12',str(current_year)+'-01',str(current_year)+'-02'], # need last year's december and this year's Jan/Feb
            'MAM': [str(current_year)+'-03',str(current_year)+'-04',str(current_year)+'-05'], # need this year for all months
            'JJA': [str(current_year)+'-06',str(current_year)+'-07',str(current_year)+'-08'], # need this year of all months
            'SON': [str(current_year)+'-09',str(current_year)+'-10',str(current_year)+'-11']}  # need this year for all months as long as this is called in Dec (not Jan/Feb)

        # Get the month indices for the season that just ended
        season_indices = season_month_indices[last_season]
        data_files = [pathname_data+'monthly/'+s+'.nc' for s in season_indices]

    elif res == 'month':
        month_names = ['01','02','03','04','05','06','07','08','09','10','11','12']
        months = range(1,13)
        last_season_index = current_month - 2  # -2 because 1 for last month and 1 for 0-based index
        # here need to merge the daily files into a monthly file
        if current_month == date.today().month:
            utils.daily_to_monthly(str(current_year),month_names[last_season_index],incomplete)
        data_files = [pathname_data+'monthly/'+str(current_year)+'-'+month_names[last_season_index]+'.nc']
        if last_season_index < 0:  # need to get last year's
            data_files = [pathname_data+'monthly/'+str(current_year-1)+'-'+month_names[last_season_index]+'.nc']

    if region == 'ARCC':  # specific boundaries and locations for map
        regions = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
        places = [(63.748651, -68.515855),(62.809285, -92.086992),(76.424718, -82.889151),(69.121958, -105.058614)] 
        place_names = ['Iqaluit','Rankin Inlet','Grise Fiord','Cambridge Bay']
        place_name_locations = [(64.2, -70.7),(62.1, -91.8),(76.7, -87),(69.3, -113.5)]  # coords of labels

    norm = xr.open_dataset(pathname_data+'normals-'+str(normal_years[0])+'-'+str(normal_years[-1])+'.nc')
    szn = xr.concat([xr.open_dataset(f) for f in data_files],dim='time')
    szn = szn.sel(longitude=lons,latitude=lats,time=szn.time.dt.month.isin(months[last_season_index])).drop_duplicates(dim='time')
    norm = norm.sel(longitude=lons,latitude=lats,month_day=norm.month.isin(months[last_season_index]))

    norm['t2m'] -= 273.15
    szn['t2m'] -= 273.15
    
    T_anom, P_anom = calc_seasonal_anomalies(szn,norm)
    if region == 'ARCC':
        print("Total T anomaly for the region: ",mask_anomalies(T_anom,'T').values,"deg C")
        print("Total P anomaly for the region: ",mask_anomalies(P_anom,'P').values,"%")

    plot_anomalies_tif(T_anom,'T')
    plot_anomalies_tif(P_anom,'P')
