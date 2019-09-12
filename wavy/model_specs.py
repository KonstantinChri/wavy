"""
file to specify model specifications such that models can be added 
and data can be imported easily
"""

from datetime import datetime, timedelta

model_dict={'ARCMFC':
            {'Hs':'VHM0',
            'lons':'lon',
            'lats':'lat',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path':('/lustre/storeA/project/'
                    + 'copernicus/sea/mywavewam8r625/arctic/'),
            #'file_template':'%Y%m%d_MyWaveWam8r625_b%Y%m%d.nc',
            'file_template':'_MyWaveWam8r625_b%Y%m%d.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=stere +lon_0=-45 +lat_0=90 +k=1 "
                    + "+R=6371000 +no_defs")
            },
        'ARCMFCnew':
            {'Hs':'VHM0',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path':('/lustre/storeB/users/anac/HINDCAST2017/BETAMAX1.20/'),
            'file_template':'%Y%m%d00.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=stere +lon_0=-45 +lat_0=90 +k=1 "
                    + "+R=6371000 +no_defs")
            },
        'ARCMFC3':
            {'Hs':'VHM0',
            'Tp':'VTPK',
            'lons':'lon',
            'lats':'lat',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path':('/lustre/storeA/project/copernicus/'
                    + 'sea/mywavewam3/arctic/%Y/%m/'),
            #'file_template':'%Y%m%d%h_MyWaveWam3_b%Y%m%dT%h.nc',
            # Best guess: 2019071500_MyWaveWam3_b20190715T06.nc
            # - This is actually 2019071500_*_b20190715T00* but due
            #   to delay the bulletin date/time is adjusted
            'file_template':'_MyWaveWam3_b%Y%m%dT%H.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=stere +lon_0=-45 +lat_0=90 +k=1 "
                    + "+R=6371000 +no_defs")
            },
        'ww3bench':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/benchmark/0060-060-060-015/'),
            'path':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/benchmark/0060-060-060-015/'),
            'file_template':'ww3.%Y%m%d.nc',
            'basetime':datetime(1990,1,1),
            'units_time':'days since 1990-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'ww3':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/test_season/'),
            'path':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/test_season/'),
            'file_template':'ww3.%Y%m%d.nc',
            'basetime':datetime(1990,1,1),
            'units_time':'days since 1990-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'ww3_test':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/test_season_large_time_step/'),
            'path':('/lustre/storeB/project/fou/om/'
                            + 'WW3/EXP/test_season_large_time_step/'),
            'file_template':'ww3.%Y%m%d.nc',
            'basetime':datetime(1990,1,1),
            'units_time':'days since 1990-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'mwam3':
            {'Hs':'VHM0',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/' +
                           'archive/projects/metproduction/' +
                           'DNMI_WAVE/%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/DNMI_WAVE/'),
            #'file_template':'MyWave_wam3_WAVE_%Y%m%dT%HZ.nc',
            'file_template':'MyWave_wam3_WAVE_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':( "+proj=ob_tran +o_proj=longlat +lon_0=-40"
                    + " +o_lat_p=25 +R=6.371e+06 +no_defs")
            },
        'mwam3_coords':
            {
                'lons':'longitude',
                'lats':'latitude',
                'pathtofile':'/lustre/storeB/users/anac/A3km/inputfile/TRUEcoordDepthA3km.nc'
            },
        'mwam4':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/' +  
                           'archive/projects/metproduction/' + 
                           'DNMI_WAVE/%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' + 
                    'projects/metproduction/DNMI_WAVE/'),
            #'file_template':'MyWave_wam4_WAVE_%Y%m%dT%HZ.nc',
            'file_template':'MyWave_wam4_WAVE_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'mwam8':
            {'Hs':'VHM0',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/' +
                           'archive/projects/metproduction/' +
                           'DNMI_WAVE/%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/DNMI_WAVE/'),
            #'file_template':'MyWave_wam8_WAVE_%Y%m%dT%HZ.nc',
            'file_template':'MyWave_wam8_WAVE_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=25 +R=6.371e+06 +no_defs")
#            'proj4':("+proj=stere +lon_0=-45 +lat_0=90 +k=1 "
#                    + "+R=6371000 +no_defs")
            },
        'mwam800c3':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/archive/'
                            + 'projects/metproduction/MyWavewam_800m/'
                            + '%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/MyWavewam_800m/'),
            'file_template':'MyWave_wam800_c3WAVE%H.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-8 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'mwam800c2':
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/archive/'
                            + 'projects/metproduction/MyWavewam_800m/'
                            + '%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/MyWavewam_800m/'),
            'file_template':'MyWave_wam800_c2WAVE%H.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'mwam4force':
            {'u10':'Uwind',
            'v10':'Vwind',
            'lons':'lon',
            'lats':'lat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/' +
                           'archive/projects/metproduction/' +
                           'DNMI_WAVE/%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/DNMI_WAVE/'),
            'file_template':'W4km_force_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=22 +R=6.371e+06 +no_defs")
            },
        'mwam8force':
            {'u10':'Uwind',
            'v10':'Vwind',
            'lons':'lon',
            'lats':'lat',
            'time': 'time',
            'path_template':('/lustre/storeB/immutable/' +
                           'archive/projects/metproduction/' +
                           'DNMI_WAVE/%Y/%m/%d/'),
            'path':('/lustre/storeB/immutable/archive/' +
                    'projects/metproduction/DNMI_WAVE/'),
            'file_template':'W8km_force_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)',
            'proj4':("+proj=ob_tran +o_proj=longlat +lon_0=-40 "
                    + "+o_lat_p=25 +R=6.371e+06 +no_defs")
            },
        'ecwam':
            {'Hs':'significant_wave_height',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/vol/data/ec/'),
            'path':('/vol/data/ec/'),
            'file_template':'ecwam_%Y%m%dT%HZ.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'swanKC': # incomplete
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/lustre/storeB/project/fou/om/SWAN/' 
                            + 'Sula/OUTER/Ut/'),
            'path':('/lustre/storeB/project/fou/om/SWAN/' 
                            + 'Sula/OUTER/Ut/'),
            'file_template':'swan_%Y%m%d.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'swan_karmoy250': # incomplete
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time': 'time',
            'path_template':('/lustre/storeB/project/fou/om/SWAN/'
                            + 'KarmoyN/olejaa/'
                            + 'swan_karmoy250_bspec_3near25km/daily/'),
            'path':('/lustre/storeB/project/fou/om/SWAN/'
                            + 'KarmoyN/olejaa/'
                            + 'swan_karmoy250_bspec_3near25km/daily/'),
            'file_template':'swan_karmoy250_%Y%m%d.nc',
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'MoskNC': # NOcurrents
            {'Hs':'hs',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/users/anac/resultscurr'
                            +'/experiment/NOcurrents/'),
            'path':('/lustre/storeB/users/anac/resultscurr'
                            +'/experiment/NOcurrents/'),
            # NOcurrentsWAVE2018021401.nc, NOcurrentsWAVE2018030100.nc
            'file_template':'NOcurrentsWAVE%Y%m*.nc',
            'file_coords':('/lustre/storeB/users/anac/resultscurr/' 
                     + 'experiment/TRUEcoordDepthc1exte.nc'),
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'MoskWC': # withcurrents
            {'Hs':'hs',
            'rotlons':'rlon',
            'rotlats':'rlat',
            'time': 'time',
            'path_template':('/lustre/storeB/users/anac/resultscurr'
                            +'/experiment/withcurrents/'),
            'path':('/lustre/storeB/users/anac/resultscurr'
                            +'/experiment/withcurrents/'),
            'file_template':'withCWAVE%Y%m*.nc',
            'file_coords':('/lustre/storeB/users/anac/resultscurr/'
                    +'experiment/TRUEcoordDepthc1exte.nc'),
            'basetime':datetime(1970,1,1),
            'units_time':'seconds since 1970-01-01 00:00:00',
            'delta_t':'0000-00-00 (01:00:00)'
            },
        'Erin1W': # one way coupled experiment
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time':'time',
            'path':('/lustre/storeB/users/erinet/coup_exp_output/'
                    + 'ST3_experiments/1waycoup_direct_ST3/'),
            'path_template':('/lustre/storeB/users/erinet'
                    + '/coup_exp_output/ST3_experiments/'
                    + '1waycoup_direct_ST3/'),
            'file_template':'ww3.%Y%m%dT%H_hs.nc',
            'basetime':datetime(1990,1,1),
            'units_time':'days since 1990-01-01 00:00:00',
            'time_conventions': ('relative julian days with decimal part' 
                        + ' as parts of the day'),
            'delta_t':'3h',
            '_FillValue':9.96921e+36
            },
        'Erin2W': # two way coupled experiment
            {'Hs':'hs',
            'lons':'longitude',
            'lats':'latitude',
            'time':'time',
            'path':('/lustre/storeB/users/erinet/coup_exp_output/'
                    + 'ST3_experiments/Exp2_direct_ST3/'),
            'path_template':('/lustre/storeB/users/erinet/'
                    + 'coup_exp_output/ST3_experiments/'
                    + 'Exp2_direct_ST3/'),
            'file_template':'ww3.%Y%m%dT%H_hs.nc',
            'basetime':datetime(1990,1,1),
            'units_time':'days since 1990-01-01 00:00:00',
            'time_conventions': ('relative julian days with decimal part'
                        + ' as parts of the day'),
            'delta_t':'3h',
            '_FillValue':9.96921e+36
            }
        }

explst = ['OPEWAVE','NoCBM1.2WAVE','withCurrBM1.2WAVE','BETAM106OPEWAVE','NoCWAVE','WithCWAVE','Erin1W','Erin2W']
