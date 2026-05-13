'''
This script creates and saves the month-to-date ERA5 plots.
By default, it runs for the current month using full-month normals


Inputs:
Resolution: "month"
Region:  "ARCC" [had initially set this up so we could do other regions - not finished]
Partial: "True" or "False"  [this is to use the partial month normals or full month normals]
(Year: integer)
(Month: integer)
(Days in month: integer)  [this is the # of days in the month to use for partial month maps. was only really used for testing.]

Outputs:
.png files into the plots/Precip_percent_climatology/Month-to-date and plots/Temp_anomaly/Month-to-date folders
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
import geopandas as gp
from datetime import date
from setup import paths, vars
import sys
import utils
import calendar
import glob



def calc_seasonal_anomalies(ds,normals):
    # get anomalies based on partial or full month normals

    # first index the data based on the number of days that have passed in the month/season
    if res == "season":
        ds = ds.isel(time=slice(0,days_in_month))
        if partial:
            normals = normals.isel(month_day=slice(0,len(ds.time)))
    else:
        ds = ds.sel(time=ds['time'].dt.day.isin(range(1,days_in_month+1))) 
        if partial:
            normals = normals.sel(month_day=slice(0,days_in_month)) 
    global len_norm
    len_norm = normals.sizes['month_day']

    # anoamly calculations
    T = ds.t2m.mean(dim='time')
    T_normals = normals.t2m.groupby('month').mean()
    T_seas_norm = T_normals.mean(dim='month')
    T_anom = T - T_seas_norm

    P = ds.tp.sum(dim='time')
    P_normals = normals.tp.groupby('month').sum()
    P_seas_norm = P_normals.sum(dim='month')
    P_anom = (P / P_seas_norm)*100

    return T_anom, P_anom


def plot_anomalies(ds,var='T'):
    ''' Making the plots using stereographic projection.
    Saves them as png files in plots/Temp_anomaly/Month-to-date and plots/Precip_percent_climatology/Month-to-date
    '''
    # set up the domain
    proj=ccrs.Stereographic(central_longitude=vars['central_longitude'][region],central_latitude=vars['central_latitude'][region])
    fig = plt.figure(figsize=(11.5,8))
    fig.subplots_adjust(left=0.02, right=0.92, top=0.94, bottom=0.02)
    ax = plt.subplot(1,1,1,projection=proj)
    ax.set_facecolor('lightgrey')

    # set up plot titles
    if res == 'season':
        titles_en = ['Dec-Feb','Mar-May','Jun-Aug','Sep-Nov']
        titles_fr = ['déc-févr','mars-mai','juin-août','sept-nov']
    else:
        titles_en = ['January','February','March','April','May','June','July','August','September','October','November','December']
        titles_fr =['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre']

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
        if partial:
            if res == 'month':
                plt_title = 'Precipitation as a Percentage of Normal:  '+titles_en[current_season_index]+' 1-' + str(days_in_month)+', '+str(current_year)+' '+\
                    '\nPrécipitation en pourcentage de la normale:  '+'1-' + str(days_in_month)+' '+titles_fr[current_season_index]+' '+str(current_year)
            else:
                plt_title = 'Precipitation as a Percentage of Normal:  '+titles_en[current_season_index]+' ' +str(current_year) +' (' + str(days_in_month)+' days)'+\
                    '\nPrécipitation en pourcentage de la normale:  '+titles_fr[current_season_index]+' ' +str(current_year) +' (' + str(days_in_month)+' jours)'
        else:
            plt_title = 'Precipitation as a Percentage of Normal:  '+str(current_year)+' '+titles_en[current_season_index]+' ('+ str(days_in_month)+' days)'+\
                '\nPrécipitation en pourcentage de la normale:  '+str(current_year)+' '+titles_fr[current_season_index]+' (' + str(days_in_month)+' jours)'
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
        if partial:
            if res == 'month':
                plt_title = 'Temperature Anomaly:  '+titles_en[current_season_index]+' 1-' + str(days_in_month)+', '+str(current_year)+' '+\
                    '\nAnomalie de température:  '+'1-' + str(days_in_month)+' '+titles_fr[current_season_index]+' '+str(current_year)
            else:
                plt_title = 'Temperature Anomaly:   '+titles_en[current_season_index]+' ' +str(current_year) +' (' + str(days_in_month)+' days)'+\
                    '\nAnomalie de température:  '+titles_fr[current_season_index]+' ' +str(current_year) +' (' + str(days_in_month)+' jours)'
        else:
            plt_title = 'Temperature Anomaly:  '+str(current_year)+' '+titles_en[current_season_index]+' (' + str(days_in_month)+' days)'+\
                '\nAnomalie de température:  '+str(current_year)+' '+titles_fr[current_season_index]+' (' + str(days_in_month)+' jours)'
        plot_title_path = 'Temp_anomaly/'

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
    if res == 'month':
        fig.text(0.02,0.02,'Source: ERA5. Norm: 1991-2020, 1-'+str(len_norm)+' '+titles_en[current_season_index]+'/'+titles_fr[current_season_index],fontsize=15)
    else:
        fig.text(0.02,0.02,'Source: ERA5. Norm: 1991-2020, '+str(len_norm)+' days / jours',fontsize=15)

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
    fig.figimage(logo_resized, xo=fig.bbox.xmax-logo_resized.shape[1]-10, yo=bbox_subp.y0-logo_resized.shape[0]-8, zorder=10)

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

    # plot locations
    y_coords, x_coords = zip(*places)
    label_y, label_x = zip(*place_name_locations)
    ax.scatter(x_coords,y_coords,c='k',marker='o',transform=ccrs.PlateCarree())
    for i, txt in enumerate(place_names):
        ax.annotate(txt,(label_x[i],label_y[i]),transform=ccrs.PlateCarree(),fontsize=8.5,fontweight='bold')

    # save the figures
    if partial:
        norm_ttl = 'partial'
    else:
        norm_ttl = 'full'
    if res == 'season':
        plt.savefig(pathname+'plots/'+plot_title_path+'Season-to-date/'+str(current_year)+'-'+titles_en[current_season_index]+'-'+str(days_in_month)+'days-'+var+'-'+norm_ttl+'_season_normals.png')
    else:
        plt.savefig(pathname+'plots/'+plot_title_path+'Month-to-date/'+str(current_year)+'-'+month_names[current_season_index]+'-'+str(days_in_month)+'-'+var+'-'+norm_ttl+'_month_normals.png')



if __name__ == "__main__":  # this is what runs when you run the script
    # doing setup
    pathname = paths['pathname']
    pathname_data = paths['pathname_data']
    normal_years = vars['normals_years']
    month_names = ['01','02','03','04','05','06','07','08','09','10','11','12']
    partial = False  # setting the default to use the full month normals

    # setting up the default dates. these will be overwritten later if they were provided as manual inputs
    current_year = date.today().year
    current_month = date.today().month
    days_in_month = date.today().day - 5  # the number of days of era5 data available
    if days_in_month < 1:  # if we run this in the first few days of the month, do month-to-date of previous month
        current_month -= 1
        if current_month < 1: # it was january and we want to go to december
            current_month = 12
            current_year -= 1
        days_in_month = calendar.monthrange(current_year,current_month)[1] + days_in_month  # days in month is < 1 in this case

    # reading inputs
    if len(sys.argv) < 3:  # minimum is 3 because the first "input" is the script name
        print("Need type of plots (day, month, season) and region (ARCC, PYR, Prairies) as arguments")
        sys.exit(1)
    res = sys.argv[1]  # month or season
    region = sys.argv[2] # ARCC

    # if the inputs included the year and month, i.e. manually running instead of just using the defaults
    if len(sys.argv) > 3:
        partial = sys.argv[3]  # make the last argument True if using partial month normal
        if partial == 'False' or partial == 'false':  # booleans vs strings are weird
            partial = False

        if len(sys.argv) > 4: # this allows us to manually set the year and month if we are re-running
            try:
                current_year = int(sys.argv[4])
                current_month = int(sys.argv[5])
                days_in_month = int(sys.argv[6])
            except: 
                print("Need type of plots (month, season), region (ARCC), partial month normals (True/False), year, month, days in partial month map as arguments")
                if res == 'season':
                    print("For running season-to-date, the month argument should still be an integer (the current month).")
                sys.exit(1)

    # some more setup based on the inputs
    lons = vars['lons'][region]
    lats = vars['lats'][region]

    # some voodoo to calculate how many days of the season have passed
    if res == 'season' and len(sys.argv) < 5: # days of the season if not manually inputted
        if current_month in [5,8,11]:  # if it is May, August, November
            days_in_month = calendar.monthrange(current_year,current_month-2)[1] + calendar.monthrange(current_year,current_month-1)[1]+ days_in_month 
        elif current_month in [4,7,10]: # april, july, october
            days_in_month = calendar.monthrange(current_year,current_month-1)[1] + days_in_month 
        elif current_month == 2: # february
            days_in_month = 31 + 31 + days_in_month 
        elif current_month == 1: # january
            days_in_month = 31 + days_in_month
        else:
            print('trying to do season-to-date for month ',current_month,'. Use month-to-date instead (sorry)')
    
    # update the current monthly data file
    # i.e. get the most recent daily data and merge it into a monthly file
    utils.daily_to_monthly(str(current_year),month_names[current_month-1],True)  # the -1 is because of 0-based indexing

    # now get the relevant data files
    if res == 'season':
        season_names = ['DJF','MAM','JJA','SON']
        months = [[12, 1, 2],[3, 4, 5],[6, 7, 8],[9, 10, 11]]  # these are used later, when we're indexing the data

        # formula maps D,J, and F to 0, MAM to 1, etc.
        current_season_index = (current_month%12 // 3)
        current_season = season_names[current_season_index]

        # seasons and their corresponding months/years so that we can pull the relevant files
        season_month_indices = {
            'DJF': [str(current_year-1)+'-12',str(current_year)+'-01',str(current_year)+'-02'], # need last year's december and this year's Jan/Feb
            'MAM': [str(current_year)+'-03',str(current_year)+'-04',str(current_year)+'-05'], # need this year for all months
            'JJA': [str(current_year)+'-06',str(current_year)+'-07',str(current_year)+'-08'], # need this year of all months
            'SON': [str(current_year)+'-09',str(current_year)+'-10',str(current_year)+'-11']}  # need this year for all months as long as this is called in Dec (not Jan/Feb)

        # Get the file names for the current season
        season_indices = season_month_indices[current_season]
        data_files = [pathname_data+'monthly/'+s+'.nc' for s in season_indices]
        print("doing",res,"-to-date for",current_year,current_season)


    elif res == 'month':
        print("doing",res,"-to-date for",current_year,current_month)
        months = range(1,13)  # # these are used later, when we're indexing the data
        current_season_index = current_month - 1  # -1 for 0-based index

        # get the file name for the current month
        data_files = [pathname_data+'monthly/'+str(current_year)+'-'+month_names[current_season_index]+'.nc']
        if current_season_index < 0:  # need to get last year's
            data_files = [pathname_data+'monthly/'+str(current_year-1)+'-'+month_names[current_season_index]+'.nc']

    # making ARCC-specific place names to put on the map
    if region == 'ARCC':  # specific boundaries and locations for map
        regions = gp.read_file(pathname_data+'Inuit_Region_Region_inuite.shp') # shapefile for putting the border on the map
        places = [(63.748651, -68.515855),(62.809285, -92.086992),(76.424718, -82.889151),(69.121958, -105.058614)]  # coords of dots
        place_names = ['Iqaluit','Rankin Inlet','Grise Fiord','Cambridge Bay']  # labels
        place_name_locations = [(64.5, -70.3),(62.15, -91.8),(76.9, -87),(69, -113.5)]  # coords of labels

    # open and select the normals and the data
    norm = xr.open_dataset(pathname_data+'normals-'+str(normal_years[0])+'-'+str(normal_years[-1])+'.nc')  # open normals
    try:
        szn = xr.concat([xr.open_dataset(f) for f in data_files],dim='time')  # open data
    except:  # it will throw an error if the last month of the season hasn't started yet. 
        data_files.pop()  # remove the last file name
        szn = xr.concat([xr.open_dataset(f) for f in data_files],dim='time')  # try opening the data again
    szn = szn.sel(longitude=lons,latitude=lats,time=szn.time.dt.month.isin(months[current_season_index])).drop_duplicates(dim='time')  # select lat/lon and month(s)
    norm = norm.sel(longitude=lons,latitude=lats,month_day=norm.month.isin(months[current_season_index]))  # select lat/lon and month(s) of the normals

    # the data itself is in K. change to C
    norm['t2m'] -= 273.15
    szn['t2m'] -= 273.15
    
    # use the data and the normals to calculate anomalies
    T_anom, P_anom = calc_seasonal_anomalies(szn,norm)

    # make the plots
    plot_anomalies(T_anom,'T')
    plot_anomalies(P_anom,'P')
    print('done')
