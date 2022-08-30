# wavy imports
from wavy.satmod import satellite_class as sc
from wavy.consolidate import consolidate_class as cs
from wavy.utils import parse_date

class satellite_class():
    '''
    Class to handle netcdf files containing satellite data e.g.
    Hs[time], lat[time], lon[time]

    This class offers the following added functionality:
     - get swaths of desired days and read
     - get the closest time stamp(s)
     - get the location (lon, lat) for this time stamp
     - get Hs or 10m wind value for this time
     - region mask
    '''

    def __init__(
        self,sdate=None,mission=['s3a'],product=['cmems_L3_NRT'],
        edate=None,twin=30,download=False,path_local=None,
        region='global',nproc=1,varalias='Hs',api_url=None,
        filterData=False,poi=None,distlim=None,**kwargs):
        print('# ----- ')
        print(" ### Initializing satellite_class object ###")
        print(" ")
        # parse and translate date input
        missions = mission
        # products: either None, same as missions, or one product
        products = product
        if len(products) != len(missions):
            if len(products) == 1:
                products = products * len(missions)
            else:
                print("products and missions need to correspond")
                assert len(products) == len(missions)
        scos = []
        for i,m in enumerate(missions):
            scos.append( sc( sdate = sdate, edate = edate,
                             twin = twin, distlim = distlim,
                             mission = m, products = products[i],
                             region = region, varalias = varalias,
                             filterData = filterData, poi = poi,
                             nproc = nproc, api_url = api_url,
                             path_local = path_local,
                             **kwargs ) )
        cso = cs(scos)
        cso.rename_consolidate_object_parameters(obstype='satellite_altimeter')
        cso.rename_consolidate_object_parameters(mission='-'.join(missions))
        cso.rename_consolidate_object_parameters(product='-'.join(products))
        # attribute
        self.obsname = cso.obsname
        self.stdvarname = cso.stdvarname
        self.varalias = cso.varalias
        self.varname = cso.varname
        self.obstype = cso.obstype
        self.mission = cso.mission
        self.product = cso.product
        self.sdate = cso.sdate
        self.edate = cso.edate
        self.units = cso.units
        self.vars = cso.vars
        self.ocos = cso.ocos
