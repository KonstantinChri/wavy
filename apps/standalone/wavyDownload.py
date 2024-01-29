#!/usr/bin/env python3
"""
download satellite data from Copernicus
"""
# --- imports -------------------------------------------------------- #
# standard library imports
import click
from wavy.satellite_module import satellite_class as sc
from datetime import datetime, timedelta
import time
from pathlib import Path
from wavy.wconfig import load_or_default
# -------------------------------------------------------------------- #

# make sure that if name is name="all" then download all names for given nID

@click.command(context_settings={"ignore_unknown_options": True})
@click.option('--sd', type=str, default=None,
        help='starting date and time of your query e.g.: 2023-10-1 00')
@click.option('--ed', type=str, default=None,
        help='ending date and time of your query e.g.: 2023-10-10 00')
@click.option('--nid', type=str, default='cmems_L3_NRT',
        help='nID as specified in satellite_cfg.yaml')
@click.option('--name', type=str, default=None,
        help='name as specified in satellite_cfg.yaml,\
        if name equals "all", all names from chosen nID are considered')
@click.option('--nproc', type=int, default=None,
        help='chosen number of simultaneous processes')
@click.option('--path', type=str, default=None)

#@click.option('--search_str', type=str,
#       help='identifyer string to search for in remote directory')
 
def main(sd, ed, nid, name, path, nproc):
    """
    Wrapper for command line use of the wavy downloading functions.\n

    Here are some examples of supported files...
    The following most common missions are available from the CMEMS webpage:
            \ncmems_L3_NRT:\
            \n s3a - Sentinel-3A\
            \n s3b - Sentinel-3B\
            \n j3 - Jason-3 (reference mission)\
            \n c2 - Cryosat-2\
            \n al - SARAL/AltiKa\
            \n cfo - CFOSAT\
            \n h2b - HaiYang-2B\
            \n s6a - Sentinel-6A Michael Freilich\
            \n
    The following most common missions are available from CCIv1:
            \n
            \ncci_L2P:\
            \n j1 - Jason-1\
            \n j2 - Jason-2\
            \n j3 - Jason-3\
            \n c2 - Cryosat-2\
            \n envisat - Envisat\
            \n ers1 - European Remote-Sensing Satellite-1\
            \n ers2 - European Remote-Sensing Satellite-2\
            \n topex - TOPEX/Poseidon\
            \n al - SARAL/AltiKa\
            \n gfo - GEOSAT Follow-On\
            \n\
            \ncci_L3:\
            \n multi - multimission product 1991-2018\
            \n\

    Note that these examples are not exclusive,\n
    almost any other source could be added and exploited.
    """

    # read yaml config files:
    satellite_dict = load_or_default('satellite_cfg.yaml')
    print(satellite_dict)
    # settings
    now = datetime.now()
    
    if sd is None:
        sdate = now-timedelta(hours=24)
    else:
        sdate = datetime(int(sd[0:4]), int(sd[4:6]),
                         int(sd[6:8]), int(sd[8:10]))

    if ed is None:
        edate = now
    else:
        edate = datetime(int(ed[0:4]), int(ed[4:6]),
                         int(ed[6:8]), int(ed[8:10]))

    if name is None:
        namelst = [list(satellite_dict[nid]['name'].keys())[0]]
    elif name == 'all':
        namelst = list(satellite_dict[nid]['name'].keys())
    else:
        namelst = [name]

    if nproc is None:
        nproc = 1

    print(sdate)
    print(edate)
    print(nid)

    for n in namelst:
        print(n)
            
    twin = 30

    for name in namelst:
        
        print("Attempting to download data for:", name)
        print("Time period:", str(sdate), "to", str(edate))
        
        start_time = time.time()

        sco = sc(sd=sdate, ed=edate,
                nID=nid, name=name)
        sco.download(path=path, nproc=nproc)

        time1 = time.time() - start_time
        print("Time used for collecting data: ", time1, " seconds")

if __name__ == "__main__":
    main()
