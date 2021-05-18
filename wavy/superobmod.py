from utils import runmean_conv
from pygam import LinearGAM, l, s, ExpectileGAM
import numpy as np
from copy import deepcopy
import yaml
import os
from datetime import datetime, timedelta
import netCDF4

from utils import find_included_times

moddir = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
                        '..', 'config/variable_info.yaml'))
with open(moddir,'r') as stream:
    variable_info=yaml.safe_load(stream)

def superobbing(varalias,vardict,superob=None,outlier_detection='gam',\
missing_data='marginalize',date_incr=1,**kwargs):
    """
    Applies a smoothing filter to create a super-observed ts
    **kwargs includes method specific input for chosen smoother
    Smoother on wish list are:
            block-average
            running mean using convolution
            GP
            GAM
            ...
    Caution:    for some smoothers much more of time series has 
                to be included.
    """
    newdict = deepcopy(vardict)
    stdvarname = variable_info[varalias]['standard_name']
    # !if for satellites first a landmask has to be created!
    if outlier_detection is not None:
        ol_dict = detect_outliers(varalias,vardict,method=outlier_detection)
        newdict[stdvarname] = ol_dict['ts_clean']
    else: print('Warning: Performing outlier detection is recommended')
    if superob is not None:
        # check if outlier detection was performed if not warn
        if 'ol_dict' not in locals():
            print('Warning: not outlier detection was performed!')
        # determine the output grid
        if isinstance(date_incr,int):
        # increments are in #hours
        # create output grid --> list of time stamps depending on choice
            sd = vardict['datetime'][0]
            ed = vardict['datetime'][-1]
            steps = int((ed-sd).total_seconds()/(date_incr*60*60))+1
            tmpd = sd
            output_dates = [tmpd + timedelta(hours=i) \
                            for i in range(0,steps,date_incr) \
                            if (tmpd + timedelta(hours=i) <= ed)]
            del tmpd
        elif isinstance(date_incr,list):
            output_dates = date_incr
        else: # original datetimes are used
            output_dates = vardict['datetime']
        output_grid = netCDF4.date2num(output_dates,units=vardict['time_unit'])
        # super observations are computed from cleaned time series
        tmp_vardict = deepcopy(newdict)
        # NaNs need to be removed before calculating superobs
        tmpvar = np.array(tmp_vardict[stdvarname])
        tmptime = np.array(tmp_vardict['time'])
        tmpdtime = np.array(tmp_vardict['datetime'])
        tmptime = tmptime[~np.isnan(tmpvar)]
        tmpdtime = tmpdtime[~np.isnan(tmpvar)]
        tmpvar = tmpvar[~np.isnan(tmpvar)]
        tmp_vardict[stdvarname] = tmpvar
        tmp_vardict['time'] = tmptime
        tmp_vardict['datetime'] = tmpdtime
        sobs_ts = compute_superobs(varalias,tmp_vardict,output_grid,\
                                    output_dates,method=superob,\
                                    date_incr=date_incr,ol_dict=ol_dict)
    if missing_data == 'marginalize':
        # padding with NaNs retrieved from ol_dict['ts_clean']
        # only possible when same grid or datetimes are used
        if 'output_grid' in locals():
            print('Marginalization is not possible on given output grid')
            raise(RuntimeError)
        else:
            newdict[stdvarname][np.isnan(ol_dict['ts_clean'])] = np.nan
    elif missing_data == 'impute':
        # handle missing data
        newdict[stdvarname] = list(sobs_ts)
        newdict['time'] = list(output_grid)
        newdict['datetime'] = output_dates
        newdict['longitude'] = [vardict['longitude'][0]]*len(output_dates)
        newdict['latitude'] = [vardict['latitude'][0]]*len(output_dates)
    return newdict

def compute_superobs(varalias,vardict,output_grid,\
output_dates, method='gam', date_incr=1,**kwargs):
    print('Superobserve data with method:',method)
    stdvarname = variable_info[varalias]['standard_name']
    dt = vardict['datetime']
    x = vardict['time']
    y = vardict[stdvarname]
    X = output_grid
    if method=='gam':
        sobs_ts = so_linearGAM(x,y,X,varalias,**kwargs)
    elif method=='block_mean':
        # blocks are means from date_incr in hours
        # For each grid_input time_stamp compute mean of hour
        # if at least half of values are valid
        # else attribute NaN
        sobs_ts = block_means(dt,x,y,output_dates,date_incr)
    else: print('Method not defined, please enter valid method')
    return sobs_ts

def block_means(dt,x,y,X,date_incr):
    means = []
    if isinstance(x,list):
        x = np.array(x)
    if isinstance(y,list):
        y = np.array(y)
    for i in range(len(X)):
        # check if more than 50% of values are valid
        # if so compute mean
        idx = find_included_times(dt,\
                                  sdate=X[i]-timedelta(hours=date_incr),\
                                  edate=X[i],twin=0)
        block = y[idx]
        nominator = len(block[np.isnan(block)])
        denominator = len(block)
        if denominator == 0:
            ratio = 1
        else:
            ratio = nominator/float(denominator)
        if ratio < 0.5:
            means.append(np.nanmean(block))
        else:
            means.append(np.nan)
    means = np.array(means)
    return means

def so_linearGAM(x,y,X,varalias,**kwargs):
    if isinstance(x,list):
        x = np.array(x)
    x = x.reshape(len(x),1)
    if isinstance(y,list):
        y = np.array(y)
    if isinstance(X,list):
        X = np.array(X)
    if X is None:
        X = x.reshape(len(x),1)
    else:
        X = X.reshape(len(X),1)
    if 'n_splines' in kwargs.keys():
        n_splines = kwargs['n_splines']
    else:
        # This is because the automatic approach is too smooth
        n_splines = int(len(y)/5)
    if varalias != 'Mdir':
        gam = LinearGAM(n_splines=n_splines,\
                        terms=s(0,basis='ps')\
                        ).gridsearch(x, y)
    else:
        print('CYCLIC!')
        print(x.shape)
        print(X.shape)
        n_splines = int(len(y)/5)
        gam = LinearGAM(n_splines=n_splines,\
                        terms=s(0,basis='cp',edge_knots=[0,360])\
                        ).gridsearch(x, y)
    # sample on the input grid
    means = gam.predict(X)
    return means

def detect_outliers(varalias,vardict,method='gam',**kwargs):
    print('Detect outliers with method:', method)
    stdvarname = variable_info[varalias]['standard_name']
    ol_dict={}
    dt = vardict['datetime']
    x = vardict['time']
    y = vardict[stdvarname]
    # coars use approximate limits (in future use range from yaml)
    llim = variable_info[varalias]['valid_range'][0]
    ulim = variable_info[varalias]['valid_range'][1]
    # rogorous removal use techniques like: 
    # blockVariance, GP, GAM, (quantile regression) random forest, ...
    if method=='gam':
        idx = ol_linearGAM(x,y,varalias,**kwargs)
        ts_clean = np.array(y)
        ts_clean[idx] = np.nan
    if method=='expectile':
        idx = ol_expectileGAM(x,y,varalias,**kwargs)
        ts_clean = np.array(y)
        ts_clean[idx] = np.nan
    ol_dict['indices']=idx
    ol_dict['ts_clean']=ts_clean
    return ol_dict

def ol_expectileGAM(x,y,varalias,**kwargs):
    if isinstance(x,list):
        x = np.array(x)
    if isinstance(y,list):
        y = np.array(y)
    X = x.reshape(len(x),1)
    if 'n_splines' in kwargs.keys():
        n_splines = kwargs['n_splines']
    else:
        # This is because the automatic approach is too smooth
        n_splines = int(len(y)/5)
    gam50 = ExpectileGAM(expectile=0.50,terms=s(0),\
                        n_splines=n_splines).gridsearch(X, y)
    # This practice of copying makes the models 
    # less likely to cross and much faster
    # https://pygam.readthedocs.io/en/latest/notebooks/tour_of_pygam.html
    # and copy the smoothing to the other models
    lam = gam50.lam
    # now fit a few more models
    gam95 = ExpectileGAM(expectile=0.95, lam=lam, terms=s(0),\
                        n_splines=n_splines).fit(X, y)
    gam05 = ExpectileGAM(expectile=0.05, lam=lam, terms=s(0),\
                        n_splines=n_splines).fit(X, y)
    ulim = gam95.predict(X)
    llim = gam05.predict(X)
    idx = [i for i in range(len(y)) \
            if (y[i]>ulim[i,1] or y[i]<llim[i])]
    return idx

def ol_linearGAM(x,y,varalias,**kwargs):
    if isinstance(x,list):
        x = np.array(x)
    if isinstance(y,list):
        y = np.array(y)
    X = x.reshape(len(x),1)
    if 'n_splines' in kwargs.keys():
        n_splines = kwargs['n_splines']
    else:
        # This is because the automatic approach is too smooth
        n_splines = int(len(y)/5)
    if varalias != 'Mdir':
        gam = LinearGAM(n_splines=n_splines,\
                        terms=s(0,basis='ps')\
                        ).gridsearch(X, y)
    else:
        print('CYCLIC!')
        print(x.shape)
        print(X.shape)
        n_splines = int(len(y)/5)
        gam = LinearGAM(n_splines=n_splines,\
                        terms=s(0,basis='cp',edge_knots=[0,360])\
                        ).gridsearch(X, y)
    #gam = LinearGAM(n_splines=n_splines,terms=s(0)).gridsearch(X, y)
    # sample on the input grid
    means = gam.predict(X)
    bounds = gam.prediction_intervals(X, width=.95)
    idx = [i for i in range(len(y)) \
            if (y[i]>bounds[i,1] or y[i]<bounds[i,0])]
    return idx
