# change path names
paths = {'pathname_data': '/home/psotkaj/clim4/era5-data/' ,
         'pathname': '/home/psotkaj/era5_for_arcc/',
         'pathname_shiny':'/home/psotkaj/shiny-server/'
        }

# change variables for plots here if desired
vars = {'lats_full': slice(85,41),
        'lons_full': slice(-170,-52),
        'normals_years': range(1991,2021), #1991-2020 normals period
        'lats' : {'ARCC': slice(84,53)},
        'lons' : {'ARCC':slice(-142,-55)},
        'central_longitude': {'ARCC':262},
        'central_latitude':{'ARCC':70}
}

# do not change these! used for pulling era5 data for all of Canada.
vars_for_api = {'lats': slice(85,41),
        'lons': slice(-170,-52),
        'area_era5': [85,-170,41,-52]
        }