'''
This script creates and saves the seasonal and monthly ERA5 plots.
By default, it runs for the most recent month/season

Inputs:
Resolution: "month" or "season"
Region: "ARCC" [had initially set this up so we could do other regions - not finished]

(Year: integer)
(Month: integer)
(Incomplete: "True" or "False") [deprecated]

Outputs:
.png files into the plots/Precip_percent_climatology and plots/Temp_anomaly folders
.tif files into the tif_plots folder which also get copied into [pathname_shiny]/Project-Climate-Bulletin-ERA5/figs/
values for avg temp anomaly and avg precip % climatology for Inuit land region (for ARCC presentation). Printed on screen/output in log file.
'''

from matplotlib import pyplot as plt
import numpy as np
import matplotlib as mpl
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
import subprocess
from osgeo import gdal, osr
import shutil
import subprocess


def warp_for_web(ds,var):
    '''add coordinate points to the plots in tif_plots/, 
    warp them for web display on bulletin dashboard,
    copy files to shiny-server/Project-Climate-Bulletin-ERA5/figs/ so that dashboard can use them.
    current dashboard addresses: http://mencius.pacific.int.ec.gc.ca:3838/sci/psotkaj/
    '''
    if res == 'month':
        orig_fn = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'.tif'
        output_fn = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'-anom.tif'
        output_final = 'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'-final.tif'
    else:
        orig_fn = 'tif_plots/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+'.tif'  # todo:
        output_fn = 'tif_plots/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+'-anom.tif'
        output_final = 'tif_plots/'+str(current_year)+'-'+last_season+'-'+var+'-final.tif'
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

    # Reproject image from EPSG4326 to EPSG3857
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
    # copy new plots to shiny server directory

    source_files = glob.glob(pathname+'tif_plots/*final.tif')
    for file_path in source_files:
        try:
            shutil.copy(file_path, paths['pathname_shiny']+'Project-Climate-Bulletin-ERA5/figs/')
        except Exception as e:
            print(f"Error copying {file_path}: {e}")


def calc_anomalies(ds,normals):
    # subtract the normals from T to get anomalies
    T = ds.t2m.mean(dim='time')
    T_normals = normals.t2m.groupby('month').mean()
    T_seas_norm = T_normals.mean(dim='month')
    T_anom = T - T_seas_norm

    # divide P by the normals to get % of climatology
    P = ds.tp.sum(dim='time')
    P_normals = normals.tp.groupby('month').sum()
    P_seas_norm = P_normals.sum(dim='month')
    P_anom = (P / P_seas_norm)*100

    return T_anom, P_anom


def mask_anomalies(ds,var='T'):
    # apply mask for Inuit land region to get averages for T and P
    regions_file = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')
    regions=gp.GeoDataFrame(columns=['set'],geometry=[regions_file.union_all()])

    mask = regionmask.mask_3D_geopandas(regions, ds.longitude, ds.latitude)
    ds = ds.where(mask.sel(region=0))

    if var == 'T':
        return np.round(ds.mean(),2)
    else:
        return np.round(ds.mean(),0)

def plot_anomalies(ds,var='T'):
    ''' Making the plots using stereographic projection.
    Saves them as png files in plots/Temp_anomaly and plots/Precip_percent_climatology
    '''
    # set up the domain
    proj=ccrs.Stereographic(central_longitude=vars['central_longitude'][region],central_latitude=vars['central_latitude'][region])
    fig = plt.figure(figsize=(11.5,8))
    fig.subplots_adjust(left=0.02, right=0.92, top=0.94, bottom=0.02)
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

    if var =='P':
        # precip colourbar settings
        vmin = 0
        vmax = 300  # default colourbar goes up to 300% for precip
        extend = 'max' # so there's an arrow at the upper end
        centre_value = 100  # this is so that the white colour is in the middle
        cbar_levels = [0,25,50,75,90,110,125,150,175,200,250,300]  # manually choose where the divisions are
        cmap = utils.create_colormap()['precip_BrGBg']

        # title for the plot and for the filename
        plt_title = 'Precipitation as a Percentage of Normal:  '+titles_en[last_season_index]+' '+str(current_year)+\
                '\nPrécipitation en pourcentage de la normale:  '+titles_fr[last_season_index]+' '+str(current_year)
        plot_title_path = 'Precip_percent_climatology/'
    else:
        # temp colourbar settings
        vmin = -10  # default starts at -10 and goes to +10
        vmax = 10
        extend = 'both'  # arrow at upper and lower ends
        centre_value = 0  # so that 0 is the white colour
        cbar_levels = np.arange(vmin,vmax+1,1)  # can change the last number here if you want increments other than 1 deg
        cbar_levels = np.delete(cbar_levels,np.where(cbar_levels==0))  # this is so that the -1 to 0 and 0 to +1 increments are both white
        cmap = utils.create_colormap()['temp_ROYCB']
        
        # title for the plot and for the filename
        plt_title = 'Temperature Anomaly:  '+titles_en[last_season_index]+' '+str(current_year)+\
            '\nAnomalie de température:  '+titles_fr[last_season_index]+' '+str(current_year)
        plot_title_path = 'Temp_anomaly/'

    if incomplete:  # [deprecated]
        plt_title += ' -TO-DATE'

    # setting up the colourbar axis
    # normalizing the colourbar values to map the range to [0,1]
    divnorm = mpl.colors.TwoSlopeNorm(vcenter=centre_value, vmax=vmax, vmin=vmin)

    # this is the line that actually plots the data
    cs = ax.contourf(ds.longitude,ds.latitude,ds,transform=ccrs.PlateCarree(),
                     cmap=cmap,norm=divnorm,levels=cbar_levels,extend=extend)
    
    # insert colour bar, can change the orientation, size, and position of it
    cax = inset_axes(ax, width="3%", height="95%", loc='right', borderpad=-3)
    cbar = fig.colorbar(cs, cax=cax, orientation='vertical')

    # inserting tick marks, title on the colourbar
    cbar.ax.tick_params(labelsize=13)
    cbar.set_ticks(cbar_levels)
    if var == 'T':
        cbar.ax.set_title(label=r"$^\circ$C",fontsize=16,pad=10)
    else:
        cbar.ax.set_title(label=r"%",fontsize=16,pad=10)

    # add plot title and the text at the bottom
    ax.set_title(plt_title,fontsize=22,loc='left')
    fig.text(0.02,0.02,'Source: ERA5. Norm: 1991-2020',fontsize=15)

    # adding boundary lines and stuff
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_0_boundary_lines_land', scale='50m', facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature(category='cultural', 
        name='admin_1_states_provinces_lines', scale='50m',facecolor='none', edgecolor='k',alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', \
        scale='50m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))
    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'lakes', \
        '110m', edgecolor='k', facecolor='none', alpha=0.5,linewidth=0.5))
    
    # add ECCC logo
    logo = mpimg.imread(pathname_data+'eccc_logo.png')
    logo_resized = zoom(logo,(0.4,0.4,1))
    bbox_subp = ax.get_window_extent()
    fig.figimage(logo_resized, xo=fig.bbox.xmax-logo_resized.shape[1]-10, yo=bbox_subp.y0-logo_resized.shape[0]-8, zorder=10)  # position of logo
    if incomplete:  # [deprecated]
        fig.text(0.9,0.97,'to date ' + (datetime.today()-timedelta(days=5)).strftime("%m-%d"),fontsize=11) 

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
    gl2.ylocator = mticker.FixedLocator([lats.stop,lats.start])
    gl2.xlocator = mticker.FixedLocator([lons.stop,lons.start])

    # plot ARCC specific locations
    y_coords, x_coords = zip(*places)
    label_y, label_x = zip(*place_name_locations)
    ax.scatter(x_coords,y_coords,c='k',marker='o',transform=ccrs.PlateCarree())
    for i, txt in enumerate(place_names):
        ax.annotate(txt,(label_x[i],label_y[i]),transform=ccrs.PlateCarree(),fontsize=8.5,fontweight='bold')

    # save the figures
    if incomplete:  # [deprecated]
        file_ending = '-to-date.png'
    else:
        file_ending = '.png'
    if res == 'season':
        plt.savefig(pathname+'plots/'+plot_title_path+'Seasonal/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+file_ending)
    else:
        plt.savefig(pathname+'plots/'+plot_title_path+'Monthly/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+file_ending)

def plot_anomalies_tif(ds,var='T'):
    ''' Making the plots using epsg projection.
    Saves them as tif files in tif_plots/
    Only touch this if you want to change the plots that go on the test dashboards
    '''
    proj=ccrs.epsg(3857)
    fig = plt.figure(figsize=(10,10))  # don't change resolution or size because of hard-coded GCPs
    fig.subplots_adjust(left=0.02, right=0.92, top=0.94, bottom=0.02)
    place_names = ['Iqaluit','Rankin Inlet','Grise Fiord','Cambridge Bay']
    place_name_locations = [(64.2, -70.7),(62.1, -91.8),(76.7, -87),(69.3, -113.5)]  # coords of labels

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
        cmap = utils.create_colormap()['precip_BrGBg']
        plt_title = 'Precipitation as a Percentage of Normal:  '+str(current_year)+' '+titles_en[last_season_index]+\
                '\nPrécipitation en pourcentage de la normale:  '+str(current_year)+' '+titles_fr[last_season_index]
    else:
        vmin = -10
        vmax = 10
        extend = 'both'
        centre_value = 0
        cbar_levels = np.arange(vmin,vmax+1,1)
        cbar_levels = np.delete(cbar_levels,np.where(cbar_levels==0))
        cmap = utils.create_colormap()['temp_ROYCB']
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
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+titles_en[last_season_index]+'-'+var+'.tif')
    else:
        plt.savefig(pathname+'tif_plots/'+str(current_year)+'-'+month_names[last_season_index]+'-'+var+'.tif')
    warp_for_web(ds,var)


if __name__ == "__main__":  # this is what runs when you run the script
    # doing setup
    pathname = paths['pathname']
    pathname_data = paths['pathname_data']
    normal_years = vars['normals_years']
    incomplete = False  # this is a flag for if the month that's running is incomplete or not [deprecated]
    
    # reading inputs
    if len(sys.argv) < 3:  # minimum is 3 because the first "input" is the script name
        print("Need type of plots (day, month, season) and region (ARCC, PYR, Prairies) as arguments")
        sys.exit(1)
    res = sys.argv[1]  # month or season
    region = sys.argv[2] # ARCC

    # if the inputs included the year and month, i.e. manually running instead of just using the defaults
    if len(sys.argv) > 3:  # this allows us to manually set the year and month if we are re-running
        current_year = int(sys.argv[3])
        current_month = int(sys.argv[4])+1  # there's a +1 here because it's set up to run the previous month. so if the input is 4, in order to make the april plot we have to pretend that it's currently may
        if len(sys.argv) > 5:
            incomplete = sys.argv[5]  # [deprecated]
    else:  # otherwise, take today's year and month
        current_year = date.today().year
        current_month = date.today().month

    # some more setup stuff based on the inputs
    lons = vars['lons'][region]
    lats = vars['lats'][region]
    if res == 'season':
        titles_en = ['Dec-Feb','Mar-May','Jun-Aug','Sep-Nov']
        titles_fr = ['déc-févr','mars-mai','juin-août','sept-nov']
    else:
        titles_en = ['January','February','March','April','May','June','July','August','September','October','November','December']
        titles_fr =['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']

    # now get the relevant data files
    if res == 'season':
        season_names = ['DJF','MAM','JJA','SON']
        months = [[12, 1, 2],[3, 4, 5],[6, 7, 8],[9, 10, 11]]

        # formula maps D,J, and F to 0, MAM to 1, etc. then do -1 because we want the season that just ended
        # e.g. if current month is March, April, or May, we want to grab the completed DJF season
        # (if instead you want to do season-to-date, you should use the plots_mtd.py script)
        last_season_index = (current_month%12 // 3)-1
        last_season = season_names[last_season_index]

        # setting stuff up to pull the relevant file names
        #this script will run shortly after each season finishes (early March, June, Sept, Dec)
        season_month_indices = {
            'DJF': [str(current_year-1)+'-12',str(current_year)+'-01',str(current_year)+'-02'], # need last year's december and this year's Jan/Feb
            'MAM': [str(current_year)+'-03',str(current_year)+'-04',str(current_year)+'-05'], # need this year for all months
            'JJA': [str(current_year)+'-06',str(current_year)+'-07',str(current_year)+'-08'], # need this year of all months
            'SON': [str(current_year)+'-09',str(current_year)+'-10',str(current_year)+'-11']}  # need this year for all months as long as this is called in Dec (not Jan/Feb)

        # Get the file names for the season that just ended
        season_indices = season_month_indices[last_season]
        data_files = [pathname_data+'monthly/'+s+'.nc' for s in season_indices]  # a list of the monthly data files for this season

        print(last_season,current_year)

    elif res == 'month':
        month_names = ['01','02','03','04','05','06','07','08','09','10','11','12']
        months = range(1,13)
        last_season_index = current_month - 2  # -2 because -1 for previous month and -1 for 0-based index

        # this is where we merge the daily era5 files into a monthly file
        if current_month == date.today().month:
            utils.daily_to_monthly(str(current_year),month_names[last_season_index],incomplete)

        # catch for if it's january we need to subtract 1 year from current_year
        if last_season_index < 0:
            current_year -= 1

        # get the monthly data file
        data_files = [pathname_data+'monthly/'+str(current_year)+'-'+month_names[last_season_index]+'.nc']

        print(month_names[last_season_index],current_year)

    # making ARCC-specific place names to put on the map
    if region == 'ARCC':
        regions = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp')  # shapefile for putting the border on the map
        places = [(63.748651, -68.515855),(62.809285, -92.086992),(76.424718, -82.889151),(69.121958, -105.058614)] # coords of dots
        place_names = ['Iqaluit','Rankin Inlet','Grise Fiord','Cambridge Bay']  # labels
        place_name_locations = [(64.5, -70.3),(62.15, -91.8),(76.9, -87),(69, -113.5)]  # coords of labels

    # open and select the normals and the data
    norm = xr.open_dataset(pathname_data+'normals-'+str(normal_years[0])+'-'+str(normal_years[-1])+'.nc')  # open normals
    szn = xr.concat([xr.open_dataset(f) for f in data_files],dim='time')  # open the data files for this month/season
    szn = szn.sel(longitude=lons,latitude=lats,time=szn.time.dt.month.isin(months[last_season_index])).drop_duplicates(dim='time')  # select lat/lon and month(s)
    norm = norm.sel(longitude=lons,latitude=lats,month_day=norm.month.isin(months[last_season_index]))  # select lat/lon and month(s) of the normals

    # the data itself is in K. change to C
    norm['t2m'] -= 273.15
    szn['t2m'] -= 273.15
    
    # use the data and the normals to calculate anomalies
    T_anom, P_anom = calc_anomalies(szn,norm)
    if region == 'ARCC':
        T_value = mask_anomalies(T_anom,'T').values
        P_value = mask_anomalies(P_anom,'P').values
        print("Total T anomaly for ARCC: ",T_value,"deg C")
        print("Total P anomaly for ARCC: ",P_value,"%")

        # write the values into the anomaly_numbers_for_ARCC text file
        date_str = '\n \n' + str(current_year) + ' ' + titles_en[last_season_index] + '\n'
        T_str = str(T_value) + " deg C\n"
        P_str = str(P_value) + r" % of normal"
        with open("anomaly_numbers_for_ARCC.txt","a") as file:
            file.writelines([date_str,T_str,P_str])

    # make the plots
    plot_anomalies(T_anom,'T')
    plot_anomalies(P_anom,'P')
    # make the tif plots
    plot_anomalies_tif(T_anom,'T')
    plot_anomalies_tif(P_anom,'P')
    print('done')
