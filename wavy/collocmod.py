#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------#
"""
- Module that should take care of collocation of points or swaths
- Needs input from modules that retrieve from observational platforms
  and models
"""
# --- import libraries ------------------------------------------------#
# standard library imports
import numpy as np
import netCDF4
from datetime import datetime, timedelta
import os
import time
from dateutil.relativedelta import relativedelta
import pyresample
from tqdm import tqdm
from copy import deepcopy
import xarray as xr

# own imports
from wavy.utils import collocate_times
from wavy.utils import make_fc_dates
from wavy.utils import hour_rounder, hour_rounder_pd
from wavy.utils import NoStdStreams
from wavy.utils import parse_date
from wavy.utils import flatten
from wavy.utils import compute_quantiles
from wavy.wconfig import load_or_default
from wavy.ncmod import ncdumpMeta, get_filevarname
from wavy.modelmod import model_class as mc
from wavy.quicklookmod import quicklook_class_sat as qls
# ---------------------------------------------------------------------#

# read yaml config files:
model_dict = load_or_default('model_cfg.yaml')
insitu_dict = load_or_default('insitu_cfg.yaml')
variable_def = load_or_default('variable_def.yaml')

def collocation_fct(obs_lons, obs_lats, model_lons, model_lats):
    grid = pyresample.geometry.GridDefinition(
                                lats=model_lats,
                                lons=model_lons)
    # Define some sample points
    swath = pyresample.geometry.SwathDefinition(lons=obs_lons,
                                                lats=obs_lats)
    # Determine nearest (great circle distance) neighbour in the grid.
    valid_input_index, valid_output_index, index_array, distance_array = \
                            pyresample.kd_tree.get_neighbour_info(
                                source_geo_def=grid,
                                target_geo_def=swath,
                                radius_of_influence=1000000000,
                                neighbours=1)
    # get_neighbour_info() returns indices in the
    # flattened lat/lon grid. Compute the 2D grid indices:
    index_array_2d = np.unravel_index(index_array, grid.shape)
    return index_array_2d, distance_array, valid_output_index

def get_model_filename(nID, d, leadtime):
    mco = mc(nID, d, leadtime)
    return mco._make_model_filename_wrapper(d, leadtime)

def find_valid_fc_dates_for_model_and_leadtime(fc_dates, model, leadtime):
    '''
    Finds valid dates that are close to desired dates at a precision
    of complete hours
    '''
    fc_dates_new = hour_rounder_pd(fc_dates)
    if (leadtime is None or leadtime == 'best'):
        pass
    else:
        fc_dates_new = [d for d in fc_dates_new
                if get_model_filename(model, d, leadtime) != False]
    return fc_dates_new

def check_if_file_is_valid(fc_date, model, leadtime, max_lt=None):
    fname = get_model_filename(
                model, fc_date, leadtime, max_lt=max_lt)
    print('Check if requested file:\n', fname, '\nis available and valid')
    try:
        nc = netCDF4.Dataset(fname, mode='r')
        time = nc.variables['time']
        dt = netCDF4.num2date(time[:], time.units)
        if fc_date in list(dt):
            print('File is available and contains requested date')
            return True
        else:
            print('Desired date ' + str(fc_date) + ' is not in', fname)
            return False
    except (FileNotFoundError, OSError) as e:
        print('File is not available or does not contain requested date')
        print(e)
        return False

def get_closest_date(overdetermined_lst, target_lst):
    idx = []
    for i in range(len(target_lst)):
        diffs = np.abs([(target_lst[i]
                        - overdetermined_lst[j]).total_seconds()
                        for j in range(len(overdetermined_lst))])
        mindiff = np.min(diffs)
        idx.append(list(diffs).index(mindiff))
    return idx

def adjust_dict_for_idx(indict, idx, excl_keys_lst):
    outdict = deepcopy(indict)
    for k in indict.keys():
        if k not in excl_keys_lst:
            outdict[k] = np.array(indict[k])[idx]
    return outdict

def collocate_poi_ts(indict, model=None, distlim=None,\
    leadtime=None, date_incr=None, varalias=None, twin=None,\
    max_lt=None):
    """
    indict: mandatory - lons, lats, time, values
            optional - leadtime, distlim, date_incr
    """
    print("run: collocate_poi_ts")
    # get stdvarname
    # stdvarname = variable_info[varalias]['standard_name']
    # datetime or str
    if isinstance(indict['time'][0],str):
        poi_dtimes = [ parse_date(t) for t in indict['time'] ]
    elif isinstance(indict['time'][0],datetime):
        poi_dtimes = indict['time']
    else:
        print('no valid time/datetime format for poi')
        print('use either str or datetime')
    fc_date = make_fc_dates(poi_dtimes[0],poi_dtimes[-1],date_incr)
    # get coinciding date between fc_date and dates in obs_obj
    idx1 = collocate_times( unfiltered_t = poi_dtimes,
                                target_t = fc_date, twin = twin )
    # find valid/coinciding fc_dates
    if len(idx1) > len(fc_date):
        print('Muliple assignments within given time window')
        print('--> only closest to time stamp is chosen')
        idx_closest = get_closest_date(\
                    list(np.array(poi_dtimes)[idx1]),\
                    fc_date)
        idx1 = list(np.array(idx1)[idx_closest])
    # adjust obs_obj according to valid dates
    indict = adjust_dict_for_idx(indict, idx1, ['time_unit', 'meta', 'nID'])
    poi_dtimes = indict['time']
    # HERE
    del idx1
    # find valid dates for given leadtime and model
    fc_date = find_valid_fc_dates_for_model_and_leadtime(\
                                    fc_date, model, leadtime)
    # adjust fc_date according to obs date
    idx2 = collocate_times( unfiltered_t = fc_date,
                                target_t = poi_dtimes,
                                twin = twin )
    fc_date = list(np.array(fc_date)[idx2])
    del idx2
    # double check dates for poi based on cleaned cf_date
    idx_closest = get_closest_date(\
                  poi_dtimes,\
                  fc_date)
    indict = adjust_dict_for_idx(indict, idx_closest,
                                ['time_unit', 'meta', 'nID'])
    poi_dtimes = indict['time']
    del idx_closest
    # compute time based on time unit from variable definition
    time_unit = variable_def['time']['units']
    time = netCDF4.date2num(poi_dtimes,time_unit)
    # check if file exists and if it includes desired time and append
    model_vals = []
    model_lons = []
    model_lats = []
    obs_vals = []
    obs_lons = []
    obs_lats = []
    collocation_idx_x = []
    collocation_idx_y = []
    distance = []
    time_lst = []
    dtimes = []
    switch = 0
    for i, d in enumerate(tqdm(fc_date)):
#    for d in tqdm(range(len(fc_date))):
#    for d in range(len(fc_date)):
#        for t in range(1):
        with NoStdStreams():
            check = False
            check = check_if_file_is_valid(
                    d, model, leadtime, max_lt=max_lt)
            if check is True:
                # retrieve model
                fname = get_model_filename(model, d, leadtime)
                # get hold of variable names (done only once)
                if switch == 0:
                    meta = ncdumpMeta(fname)
                    lonsname = get_filevarname('lons', variable_def,
                                        model_dict[model], meta)
                    latsname = get_filevarname('lats', variable_def,
                                        model_dict[model], meta)
                    timename = get_filevarname('time', variable_def,
                                        model_dict[model], meta)
                    filevarname = get_filevarname(varalias, variable_def,
                                        model_dict[model], meta)
                    mlons = xr.open_dataset(fname)[lonsname].values
                    # secure lons from -180 to 180
                    mlons = ((mlons - 180) % 360) - 180
                    mlats = xr.open_dataset(fname)[latsname].values
                    # ensure matching dimension
                    if len(mlons.shape) == 1:
                        Mlons, Mlats = np.meshgrid(mlons, mlats)
                    else: Mlons, Mlats = mlons, mlats
                    switch = 1
                plon = [indict['longitude'][i]]
                plat = [indict['latitude'][i]]
                index_array_2d, distance_array, _ = \
                        collocation_fct(plon, plat, Mlons, Mlats)
                dst = xr.open_dataset(fname)[timename].values
                tidx = list(dst).index(np.datetime64(d))
                # impose distlim
                if distance_array[0]< distlim*1000:
                    idx_x = index_array_2d[0][0]
                    idx_y = index_array_2d[1][0]
                    model_lons.append(Mlons[idx_x, idx_y])
                    model_lats.append(Mlats[idx_x, idx_y])
                    vals = xr.open_dataset(fname)[filevarname]\
                                        [tidx, idx_x, idx_y].values
                    model_vals.append(vals.item())
                    obs_vals.append(indict['obs'][i])
                    obs_lons.append(indict['longitude'][i])
                    obs_lats.append(indict['latitude'][i])
                    collocation_idx_x.append(idx_x)
                    collocation_idx_y.append(idx_y)
                    distance.append(distance_array[0])
                    time_lst.append(time[i])
                    """
                    append fc_date as use of poi_dtimes like:
                    dtimes.append(poi_dtimes[d])
                    might not be correct of a time step cannot 
                    be collocated.
                    """
                    dtimes.append(d)
    results_dict = {
            'valid_date': dtimes,
            'time': time_lst,
            'time_unit': time_unit,
            'datetime': dtimes,
            'dist': distance,
            'model_values': model_vals,
            'model_lons': model_lons,
            'model_lats': model_lats,
            'obs_values': obs_vals,
            'obs_lons': obs_lons,
            'obs_lats': obs_lats,
            'collocation_idx_x': collocation_idx_x,
            'collocation_idx_y': collocation_idx_y
                }
    return results_dict


def collocate_station_ts(obs_obj=None,model=None,distlim=None,\
    leadtime=None,date_incr=None):
    """
    Some info
    """
    print("run: collocate_station_ts")
    fc_date = make_fc_dates(obs_obj.sdate,obs_obj.edate,date_incr)
    # get coinciding date between fc_date and dates in obs_obj
    idx1 = collocate_times( unfiltered_t = obs_obj.vars['datetime'],
                                target_t = fc_date, twin = obs_obj.twin )
    # find valid/coinciding fc_dates
    if len(idx1) > len(fc_date):
        print('Muliple assignments within given time window')
        print('--> only closest to time stamp is chosen')
        idx_closest = get_closest_date(\
                    list(np.array(obs_obj.vars['datetime'])[idx1]),\
                    fc_date)
        idx1 = list(np.array(idx1)[idx_closest])
    # adjust obs_obj according to valid dates
    for key in obs_obj.vars.keys():
        if (key != 'time_unit' and key !='meta'):
            obs_obj.vars[key] = list(np.array(obs_obj.vars[key])[idx1])
    # adjust again assumed fc_dates by filtered obs dates
    fc_date = obs_obj.vars['datetime']
    # find valid dates for given leadtime and model
    fc_date = find_valid_fc_dates_for_model_and_leadtime(\
                                    fc_date,model,leadtime)
    # check if file exists and if it includes desired time
    # if not check next possible file
    check = False
    for d in range(len(fc_date)):
        check = check_if_file_is_valid(fc_date[d],model,leadtime)
        if check == True:
            break
    if check == True:
        mc_obj = model_class( model=model,
                              fc_date=fc_date[d],
                              leadtime=leadtime,
                              varalias=obs_obj.varalias,
                              transform_lons=180)
        col_obj = collocation_class( mc_obj_in=mc_obj,
                                     obs_obj_in=obs_obj,
                                     distlim=distlim )
        model_vals = [col_obj.vars['model_values'][0]]
        tmpdate = hour_rounder(col_obj.vars['datetime'][0])
        model_datetime = [ datetime(tmpdate.year,
                                    tmpdate.month,
                                    tmpdate.day,
                                    tmpdate.hour) ]
        model_time = [netCDF4.date2num(model_datetime[0],
                        units=col_obj.vars['time_unit'])]
    if check == False:
        print('No valid model file available!')
    else:
        print('Collocating and appending values ...')
        for i in tqdm(range(d+1,len(fc_date))):
            with NoStdStreams():
                try:
                    check = check_if_file_is_valid(fc_date[i],model,leadtime)
                    if check == False:
                        raise FileNotFoundError
                    mc_obj = model_class( model=model,
                                          fc_date=fc_date[i],
                                          leadtime=leadtime,
                                          varalias=obs_obj.varalias,
                                          transform_lons=180 )
                    model_vals.append(
                            mc_obj.vars[\
                                mc_obj.stdvarname][ \
                                    col_obj.vars['collocation_idx_x'],\
                                    col_obj.vars['collocation_idx_y']\
                                ][0] )
                    model_time.append(mc_obj.vars['time'][0])
                    model_datetime.append( datetime(\
                                mc_obj.vars['datetime'][0].year,
                                mc_obj.vars['datetime'][0].month,
                                mc_obj.vars['datetime'][0].day,
                                mc_obj.vars['datetime'][0].hour ) )
                except FileNotFoundError as e:
                    print(e)
        # potentially there are different number of values
        # for obs and model
        # double check and use only coherent datetimes
        idx2 = collocate_times( model_datetime,
                                target_t = obs_obj.vars['datetime'],
                                twin = obs_obj.twin)
        col_obj.vars['model_values'] = list(np.array(\
                                                    model_vals)[idx2])
        col_obj.vars['time'] = list(np.array(model_time)\
                                            [idx2])
        col_obj.vars['datetime'] = list(np.array(\
                                            model_datetime)[idx2])
        idx3 = collocate_times(  \
                            unfiltered_t = obs_obj.vars['datetime'],
                            target_t = col_obj.vars['datetime'],
                            twin = obs_obj.twin)
        col_obj.vars['obs_values'] = list(np.array(
                                        obs_obj.vars[
                                            obs_obj.stdvarname
                                                    ])[idx3])
    # valid_date is meaningless for ts application and set to None
    col_obj.vars['valid_date'] = None
    # inflate length of constant sized variables
    col_obj.vars['dist'] = col_obj.vars['dist']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['obs_lats'] = col_obj.vars['obs_lats']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['obs_lons'] = col_obj.vars['obs_lons']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['collocation_idx_x'] = col_obj.vars['collocation_idx_x']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['collocation_idx_y'] = col_obj.vars['collocation_idx_y']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['model_lats'] = col_obj.vars['model_lats']*\
                                    len(col_obj.vars['datetime'])
    col_obj.vars['model_lons'] = col_obj.vars['model_lons']*\
                                    len(col_obj.vars['datetime'])
    results_dict = col_obj.vars
    return results_dict


class collocation_class(qls):
    '''
    draft of envisioned collocation class object
    '''

    def __init__(self, oco=None, model=None, poi=None,
    distlim=None, leadtime=None, max_lt=None, **kwargs):
        #twin=30, distlim=6):
        print('# ----- ')
        print(" ### Initializing collocation_class object ###")
        print(" ")
        # make clones to prevent overwriting
        self.varalias = oco.varalias
        self.model = model
        self.leadtime = leadtime
        self.oco = oco
        self.nID = oco.nID
        self.obstype = str(type(oco))[8:-2]
        self.stdvarname = oco.stdvarname
        self.region = oco.region
        self.units = variable_def[self.varalias].get('units')
        self.sd = oco.sd
        self.ed = oco.ed
        self.twin = kwargs.get('twin', oco.twin)
        self.distlim = kwargs.get('distlim', 6)
        #if poi is not None:
        #    !an oco should be created!
        #    # poi is of type dict
        #    self.nID = poi['nID']
        #    self.obsname = poi['nID']
        #    self.obstype = 'POI'
        #    stdvarname = variable_info[varalias]['standard_name']
        #    self.stdvarname = stdvarname
        #    self.units = variable_info[varalias].get('units')
        #    self.sdate = parse_date(poi['time'][0])
        #    self.edate = parse_date(poi['time'][-1])
        #    self.label = self.nID
        print(" ")
        print(" ## Collocate ... ")
        for t in range(1):
#        try:
            t0 = time.time()
            results_dict = self.collocate(**kwargs)
            self.model_time = results_dict['model_time']
            # build xarray dataset from results
            ds = self._build_xr_dataset(results_dict)
            self.vars = ds
            t1 = time.time()
            print(" ")
            print(" ## Summary:")
            print(len(self.vars['time']), " values collocated.")
            print("Time used for collocation:", round(t1-t0, 2), "seconds")
            print(" ")
            print(" ### Collocation_class object initialized ###")
#        except Exception as e:
#            print(e)
#            self.error = e
#            print ("! No collocation_class object initialized !")
        # add class variables
        print('# ----- ')

    def _build_xr_dataset(self, results_dict):
        ds = xr.Dataset({
                'time': xr.DataArray(
                        data=results_dict['obs_time'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['time'],
                        ),
                'dist': xr.DataArray(
                        data=results_dict['dist'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['dist'],
                        ),
                'obs_values': xr.DataArray(
                        data=results_dict['obs_values'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def[self.varalias],
                        ),
                'obs_lons': xr.DataArray(
                        data=results_dict['obs_lons'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['lons'],
                        ),
                'obs_lats': xr.DataArray(
                        data=results_dict['obs_lats'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['lats'],
                        ),
                'model_values': xr.DataArray(
                        data=results_dict['model_values'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def[self.varalias],
                        ),
                'model_lons': xr.DataArray(
                        data=results_dict['model_lons'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['lons'],
                        ),
                'model_lats': xr.DataArray(
                        data=results_dict['model_lats'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['lats'],
                        ),
                'colidx_x': xr.DataArray(
                        data=results_dict['collocation_idx_x'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['colidx_x'],
                        ),
                'colidx_y': xr.DataArray(
                        data=results_dict['collocation_idx_y'],
                        dims=['time'],
                        coords={'time': results_dict['obs_time']},
                        attrs=variable_def['colidx_y'],
                        ),
                    },
                attrs={'title': str(type(self))[8:-2] + ' dataset'}
                )
        return ds

    def _collocate_field(self, mco, tmp_dict, **kwargs):
    #mc_obj=None,obs_obj=None,col_obj=None,distlim=None,
    #datein=None,model_lats=None,model_lons=None,
    #model_vals=None,twin=None):
        """
        Some info
        """
        Mlons = mco.vars.lons
        Mlats = mco.vars.lats
        Mvars = mco.vars[mco.varalias]
        if len(Mlons.shape) > 2:
            Mlons = Mlons[0, :].data.squeeze()
            Mlats = Mlats[0, :].data.squeeze()
            Mvars = Mvars[0, :].data.squeeze()
        else:
            Mlons = Mlons.data.squeeze()
            Mlats = Mlats.data.squeeze()
            Mvars = Mvars.data.squeeze()
        obs_vars = tmp_dict[self.varalias]
        obs_lons = tmp_dict['lons']
        obs_lats = tmp_dict['lats']
        # Compare wave heights of satellite with model with
        #   constraint on distance and time frame
        print("Perform collocation with distance limit\n",
              "distlim:", self.distlim)
        index_array_2d, distance_array, _ =\
                                    collocation_fct(
                                    obs_lons, obs_lats,
                                    Mlons, Mlats)
        # caution: index_array_2d is tuple
        # impose distlim
        dist_idx = np.where((distance_array < self.distlim*1000) &
                            (~np.isnan(Mvars[index_array_2d[0],
                             index_array_2d[1]])))[0]
        idx_x = index_array_2d[0][dist_idx]
        idx_y = index_array_2d[1][dist_idx]
        results_dict = {
                'dist': list(distance_array[dist_idx]),
                'model_values': list(Mvars[idx_x, idx_y]),
                'model_lons': list(Mlons[idx_x, idx_y]),
                'model_lats': list(Mlats[idx_x, idx_y]),
                'obs_values': list(obs_vars[dist_idx]),
                'obs_lons': list(obs_lons[dist_idx]),
                'obs_lats': list(obs_lats[dist_idx]),
                'collocation_idx_x': list(idx_x),
                'collocation_idx_y': list(idx_y),
                }
        return results_dict


    def _collocate_track(self, **kwargs):
        """
        Some info
        """
        print("run: _collocate_track")

        # use only dates with a model time step closeby
        # given the time constrains
        print('Filtering valid dates ...')
        t1 = time.time()

        ndt = self.oco.vars.time.data
        ndt_datetime = [parse_date(str(d)) for d in ndt]

        ndt_valid = find_valid_fc_dates_for_model_and_leadtime(
                                    ndt, self.model, self.leadtime)

        ndt_valid = np.unique(ndt_valid)
        fc_date = ndt_valid
        t2 = time.time()

        print(f'... done, used {t2-t1:.2f} seconds')

        print("Start collocation ...")
        results_dict = {
                'model_time': [],
                'obs_time': [],
                'dist': [],
                'model_values': [],
                'model_lons': [],
                'model_lats': [],
                'obs_values': [],
                'obs_lons': [],
                'obs_lats': [],
                'collocation_idx_x': [],
                'collocation_idx_y': [],
                }
        for i in tqdm(range(len(fc_date))):
#        for i in range(len(fc_date)):
#            for f in range(1):
#            with NoStdStreams():
                for t in range(1):
#                try:
                    # filter needed obs within time period
                    target_date = [parse_date(str(fc_date[i]))]
                    idx = collocate_times(ndt_datetime,
                                          target_t=target_date,
                                          twin=self.twin)

                    print(len(idx), "footprints to be collocated")
                    # make tmp obs_obj with filtered data
                    tmp_dict = {}
                    tmp_dict['time'] = self.oco.vars['time'].values[idx]
                    tmp_dict['lats'] = self.oco.vars['lats'].values[idx]
                    tmp_dict['lons'] = self.oco.vars['lons'].values[idx]
                    tmp_dict[self.oco.varalias] = \
                            self.oco.vars[self.oco.varalias].values[idx]
                    mco = mc(sd=fc_date[i], ed=fc_date[i], nID=self.model,
                             leadtime=self.leadtime, varalias=self.varalias,
                             **kwargs)
                    mco = mco.populate(**kwargs)
                    results_dict_tmp = self._collocate_field(
                                            mco, tmp_dict, **kwargs)
                    # append to dict
                    results_dict['model_time'].append(fc_date[i])
                    results_dict['obs_time'].append(tmp_dict['time'])
                    results_dict['dist'].append(
                            results_dict_tmp['dist'])
                    results_dict['model_values'].append(
                            results_dict_tmp['model_values'])
                    results_dict['model_lons'].append(
                            results_dict_tmp['model_lons'])
                    results_dict['model_lats'].append(
                            results_dict_tmp['model_lats'])
                    results_dict['obs_values'].append(
                            results_dict_tmp['obs_values'])
                    results_dict['obs_lats'].append(
                            results_dict_tmp['obs_lats'])
                    results_dict['obs_lons'].append(
                            results_dict_tmp['obs_lons'])
                    results_dict['collocation_idx_x'].append(
                                    results_dict_tmp['collocation_idx_x'])
                    results_dict['collocation_idx_y'].append(
                                    results_dict_tmp['collocation_idx_y'])
                    if 'results_dict_tmp' in locals():
                        del results_dict_tmp
#                except (ValueError,FileNotFoundError,OSError) as e:
#                    # ValueError, pass if no collocation
#                    # FileNotFoundError, pass if file not accessible
#                    # OSError, pass if file not accessible from thredds
#                    print(e)
        # flatten all aggregated entries
        results_dict['model_time'] = results_dict['model_time']
        results_dict['obs_time'] = flatten(results_dict['obs_time'])
        results_dict['dist'] = flatten(results_dict['dist'])
        results_dict['model_values'] = flatten(results_dict['model_values'])
        results_dict['model_lons'] = flatten(results_dict['model_lons'])
        results_dict['model_lats'] = flatten(results_dict['model_lats'])
        results_dict['obs_values'] = flatten(results_dict['obs_values'])
        results_dict['obs_lats'] = flatten(results_dict['obs_lats'])
        results_dict['obs_lons'] = flatten(results_dict['obs_lons'])
        results_dict['collocation_idx_x'] = flatten(
                                    results_dict['collocation_idx_x'])
        results_dict['collocation_idx_y'] = flatten(
                                results_dict['collocation_idx_y'])
        return results_dict


    def collocate(self, **kwargs):
        """
        get obs value for model value for given
            temporal and spatial constraints
        """
        if (self.oco is None and len(self.oco.vars[self.oco.stdvarname]) < 1):
            raise Exception ('\n###\n'
                            +'Collocation not possible, '
                            +'no observation values for collocation!'
                            +'\n###'
                            )
        if (self.model is None):
            raise Exception ('\n###\n'
                            +'Collocation not possible, '
                            +'no model available for collocation!'
                            +'\n###'
                            )
        if ((self.model is not None) and (self.oco is not None)):
            results_dict = self._collocate_track(**kwargs)
        # same needed for insitu, multiins, multisat, consolidate
        return results_dict


    def quicklook(self, a=False, projection=None, **kwargs):
        # set plots
        m = kwargs.get('m', a)
        ts = kwargs.get('ts', a)
        sc = kwargs.get('sc', a)
        if m:
            import cartopy.crs as ccrs
            import cmocean
            import matplotlib.pyplot as plt
            import matplotlib.cm as mplcm
            from mpl_toolkits.axes_grid1.inset_locator import inset_axes
            lons = self.vars['obs_lons']
            lats = self.vars['obs_lats']
            var = self.vars['obs_values']
            if projection is None:
                projection = ccrs.PlateCarree()
            vartype = variable_def[self.varalias].get('type', 'default')
            if kwargs.get('cmap') is None:
                if vartype == 'cyclic':
                    cmap = mplcm.twilight
                else:
                    cmap = cmocean.cm.amp
            else:
                cmap = kwargs.get('cmap')
            lonmax,lonmin = np.nanmax(lons),np.nanmin(lons)
            latmax,latmin = np.nanmax(lats),np.nanmin(lats)
            fig = plt.figure()
            ax = fig.add_subplot(1, 1, 1, projection=projection)
            ax.set_extent(  [lonmin, lonmax,latmin, latmax],
                            crs = projection )
            sc = ax.scatter(lons,lats,s=10,
                            c = var,
                            marker='o', edgecolor = 'face',
                            cmap=cmap,
                            transform=ccrs.PlateCarree())
            axins = inset_axes(ax,
                       width="5%",  # width = 5% of parent_bbox width
                       height="100%",  # height : 50%
                       loc='lower left',
                       bbox_to_anchor=(1.01, 0., 1, 1),
                       bbox_transform=ax.transAxes,
                       borderpad=0,
                       )
            fig.colorbar(sc, cax=axins, label=self.varalias
                                        + ' [' + self.units + ']')
            ax.coastlines()
            gl = ax.gridlines(draw_labels=True,crs=projection,
                              linewidth=1, color='grey', alpha=0.4,
                              linestyle='-')
            gl.top_labels = False
            gl.right_labels = False
            plt.subplots_adjust(bottom=0.1, right=0.8, top=0.9)
            ax.set_title(self.obsname + ' (' + self.obstype + ')\n'
                      + 'from ' + str(self.vars['datetime'][0])
                      + ' to ' + str(self.vars['datetime'][-1]))
            #fig.suptitle('', fontsize=16) # unused
            plt.show()
        if ts:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            fig = plt.figure(figsize=(9,3.5))
            ax = fig.add_subplot(111)
            colors = ['k','orange']
            if self.obstype == 'insitu':
                ax.plot(self.vars['datetime'],self.vars['obs_values'],
                    linestyle='None',color=colors[0],
                    label='obs ( ' + self.nID + ' - '
                                   + self.sensor + ' )',
                    marker='o',alpha=.5,ms=2)
            elif self.obstype == 'satellite_altimeter':
                ax.plot(self.vars['datetime'],self.vars['obs_values'],
                    linestyle='None',color=colors[0],
                    label='obs (' + self.mission + ')',
                    marker='o',alpha=.5,ms=2)
            else:
                ax.plot(self.vars['datetime'],self.vars['obs_values'],
                    linestyle='None',color=colors[0],
                    label='obs (' + self.obsname + ')',
                    marker='o',alpha=.5,ms=2)
            ax.plot(self.vars['datetime'],self.vars['model_values'],
                    linestyle='None',color=colors[1],
                    label='model (' + self.model + ')',
                    marker='o',alpha=.8,ms=2)
            plt.ylabel(self.varalias + '[' + self.units + ']')
            plt.legend(loc='best')
            plt.tight_layout()
            #ax.set_title()
            plt.show()
        if sc:
            lq = np.arange(0.01,1.01,0.01)
            lq = kwargs.get('lq',lq)
            modq = compute_quantiles(np.array(self.vars['model_values']),lq)
            obsq = compute_quantiles(np.array(self.vars['obs_values']),lq)
            import matplotlib.pyplot as plt
            fig = plt.figure(figsize=(4,4))
            ax = fig.add_subplot(111)
            colors = ['k']
            if self.obstype == 'insitu':
                ax.plot(self.vars['obs_values'],self.vars['model_values'],
                    linestyle='None',color=colors[0],
                    marker='o',alpha=.5,ms=2)
                plt.xlabel='obs ( ' + self.nID + ' - '\
                                     + self.sensor + ' )'
            elif self.obstype == 'satellite_altimeter':
                ax.plot(self.vars['obs_values'],self.vars['model_values'],
                    linestyle='None',color=colors[0],
                    label='obs (' + self.mission + ')',
                    marker='o',alpha=.5,ms=2)
                plt.xlabel('obs ( ' + self.mission + ' )')
            elif self.obstype == 'POI':
                ax.plot(self.vars['obs_values'],self.vars['model_values'],
                    linestyle='None',color=colors[0],
                    marker='o',alpha=.5,ms=2)
                plt.xlabel('obs ( ' + self.obstype + ' )')
            else:
                ax.plot(self.vars['obs_values'],self.vars['model_values'],
                linestyle='None',color=colors[0],
                label='obs (' + self.obstype + ')',
                marker='o',alpha=.5,ms=2)
                plt.xlabel('obs ( ' + self.mission + ' )')
            # add quantiles
            ax.plot(obsq,modq,'r')
            # 45 degree line for orientation
            ax.axline((0, 0), (1, 1), lw=.5, color='grey', ls='--')
            plt.ylabel('models ( ' + self.model + ' )')
            vartype = variable_def[self.varalias].get('type', 'default')
            if vartype == 'cyclic':
                plt.xlim([0,360])
                plt.ylim([0,360])
            else:
                maxv = np.nanmax([self.vars['model_values'],
                                  self.vars['obs_values']])
                minv = 0
                plt.xlim([minv,maxv+0.15*maxv])
                plt.ylim([minv,maxv+0.15*maxv])
            ax.set_title(self.varalias + '[' + self.units + ']')
            plt.tight_layout()
            #ax.set_title()
            plt.show()

    def write_to_nc(self,pathtofile=None,file_date_incr=None):
        if 'error' in vars(self):
            print('Erroneous collocation_class file detected')
            print('--> dump to netCDF not possible !')
        else:
            print('to be implemented ...')

    def write_to_pickle(self,pathtofile=None):
        import pickle
        # writing
        pickle.dump( self, open( pathtofile, "wb" ) )
        print('collocation_class object written to:',pathtofile)
        # for reading
        # cco = pickle.load( open( pathtofile, "rb" ) )

    def validate_collocated_values(self,**kwargs):
        dtime = self.vars['datetime']
        mods = self.vars['model_values']
        obs = self.vars['obs_values']
        sdate = self.vars['datetime'][0]
        edate = self.vars['datetime'][-1]
        validation_dict = validate_collocated_values(
                                dtime,obs,mods,\
                                sdate=sdate,edate=edate,\
                                **kwargs)
        return validation_dict

def validate_collocated_values(dtime,obs,mods,**kwargs):
    target_t, sdate, edate, twin = None, None, None, None
    if ('col_obj' in kwargs.keys() and kwargs['col_obj'] is not None):
        col_obj = kwargs['col_obj']
        mods = col_obj.vars['model_values']
        obs = col_obj.vars['obs_values']
        dtime = col_obj.vars['datetime']
    # get idx for date and twin
    if 'target_t' in kwargs.keys():
        target_t = kwargs['target_t']
    if 'sdate' in kwargs.keys():
        sdate = kwargs['sdate']
    if 'edate' in kwargs.keys():
        edate = kwargs['edate']
    if 'twin' in kwargs.keys():
        twin = kwargs['twin']
    idx = collocate_times(dtime,
                          target_t=target_t,
                          sdate=sdate,
                          edate=edate,
                          twin=twin)
    mods = np.array(mods)[idx]
    obs = np.array(obs)[idx]
    results_dict = {'model_values':mods,'obs_values':obs}
    # validate
    from wavy.validationmod import validate,disp_validation
    validation_dict = validate(results_dict)
    disp_validation(validation_dict)
    return validation_dict

