from __future__ import print_function

import requests
import urllib
import time
from io import StringIO
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np
import os
from service_exception import *

secret = os.environ.get("K8S_SECRET_INTEGRAL_CLIENT_SECRET",open(os.environ['HOME']+"/.secret-client").read().strip())
secret_user = open(os.environ['HOME']+"/.secret-client-user").read().strip()
#secret_location=os.environ.get("INTEGRAL_CLIENT_SECRET",os.environ['HOME']+"/.secret-client")

def get_auth():
    #username = "integral"
    #username = "integral-limited"
    username = secret_user
    password = secret
    return requests.auth.HTTPBasicAuth(username, password)

auth=get_auth()

integral_services_server="134.158.75.161"
timesystem_endpoint = "http://cdcihn/timesystem"


def wait(f,timeout=5,ntries=30):
    ntries_left = ntries
    while ntries_left > 0:
        try:
            return f()
        except Exception as e: # or service?
            print("service exception", repr(e), "tries left", ntries_left)
            ntries_left-=1
            time.sleep(timeout)

def t2str(t):
    if isinstance(t,float):
        return "%.20lg"%t
    
    if isinstance(t,int):
        return "%i"%t
    
    if isinstance(t,str):
        return t

def scwlist(t1, t2, dr="any", debug=True):
    url=timesystem_endpoint+'/api/v1.0/scwlist/'+dr+'/'+t2str(t1)+'/'+t2str(t2)

    #url='https://analyse.reproducible.online/timesystem/api/v1.0/converttime/IJD/4000/SCWID'

    if debug:
        print("url",url)

    ntries_left = 30

    while ntries_left > 0:
        try:
            r=requests.get(url,auth=auth)

            if r.status_code!=200:
                raise ServiceException('error converting '+url+'; from timesystem server: '+str(r.text))

            try:
                return r.json()
            except:
                return r.text

        except Exception as e:
            ntries_left -= 1

            if ntries_left > 0:
                print("retrying timesystem",ntries_left,repr(e))
                time.sleep(5)
                continue
            else:
                raise

def converttime(informat,intime,outformat, debug=True):
    #url='http://'+integral_services_server+'/integral/integral-timesystem/api/v1.0/'+informat+'/'+intime+'/'+outformat
    url='http://cdcihn/timesystem/api/v1.0/converttime/'+informat+'/'+t2str(intime)+'/'+outformat
    #url='https://analyse.reproducible.online/timesystem/api/v1.0/converttime/IJD/4000/SCWID'

    if debug:
        print("url",url)

    ntries_left = 30

    while ntries_left > 0:
        try:
            r=requests.get(url,auth=auth)

            if r.status_code!=200:
                raise ServiceException('error converting '+url+'; from timesystem server: '+str(r.text))

            if outformat=="ANY":
                try:
                    return r.json()
                except:
                    pass
            return r.text

        except Exception as e:
            if 'is close' in repr(e):
                raise
                
            ntries_left -= 1

            if ntries_left > 0:
                print("retrying timesystem",ntries_left,repr(e))
                time.sleep(5)
                continue
            else:
                raise
        
    



def get_response(*args, **kwargs):
    if kwargs.get('wait', True):
        return wait(lambda :get_response(*args,**{**kwargs, 'wait':False}))
    
    theta, phi = args 

    default_kwargs= dict(
        radius=0.1,
        alpha=-1,
        epeak=600,
        emin=75,
        emax=2000,
        emax_rate=20000,
        lt=75,
        ampl=1,
        debug=False,
        target="ACS",
        model="compton",
        width=1,
        beta=-2.5,
        wait=True,
        theta=theta,
        phi=phi,
    )

    kwargs = {**default_kwargs, **kwargs}
    kwargs['lt'] = str(kwargs['lt'])

    #s = "http://134.158.75.161/integral/api/v1.0/response/direction/%.5lg/%.5lg?lt=%.5lg&model=compton&ampl=%.5lg&alpha=%.5lg&epeak=%.5lg&emin=%.5lg&emax=%.5lg&emax_rate=%.5lg" % (
    #theta, phi, lt, ampl, alpha, epeak, emin, emax, emax_rate)


    #url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg&width=%(width).5lg"
    url="http://cdcihn/response/api/v1.0/%(target)s/response?lt=%(lt)s&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg&width=%(width).5lg"
   # url="http://localhost:5556/api/v1.0/"+target+"/response?lt=%(lt).5lg&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
    url+="&emin=%(emin).5lg"
    url += "&emax=%(emax).5lg"

    url = url % kwargs

    print(url)

    r = requests.get(url,auth=auth)

    try:
        r=r.json()

        return {
			'flux':r['enflux'],
			'phflux':r['phflux'],
			'response':np.mean(r['response']),
			'response_min':np.min(r['response']),
			'response_max':np.max(r['response']),
			'rate':np.mean(r['rate']),
			'rate_min':np.min(r['rate']),
			'rate_max':np.max(r['rate']),
		}
    except Exception as e:
        raise ServiceException("problem with service: "+r.content)


def get_response_map(**kwargs):
    if kwargs.get('wait', True):
        return wait(lambda :get_response_map(**{**kwargs, 'wait':False}))

    default_kwargs = dict(alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS",kind="response",model="compton",beta=-2.5)

    kwargs = {**default_kwargs, **kwargs}
    kwargs['lt'] = str(kwargs['lt'])

    url="http://cdcihn/response/api/v1.0/%(target)s/response?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg"
    #url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg"
    url+="&emin=%(emin).5lg"
    url+="&emax=%(emax).5lg"
    url+="&emax_rate=%(emax_rate).5lg"
    

    url = url % kwargs
    print(url)
    
    try:
        r = requests.get(url,auth=auth)
        r = r.json()
    except Exception as e:
        print("problem",e)
        print(r.text)
        raise

    return r[kwargs['kind']]


def get_sc(utc, ra=0, dec=0, debug=False):
    s = "http://cdcihn/scsystem/api/v1.0/sc/" + utc + "/%.5lg/%.5lg" % (ra, dec)
    #s = "http://134.158.75.161/integral/integral-sc-system/api/v1.0/" + utc + "/%.5lg/%.5lg" % (ra, dec)
    if debug:
        print(s)
    r = requests.get(s,auth=auth,timeout=300)
    try:
        return r.json()
    except Exception as e:
        print(r.content)
        raise ServiceException(e,r.content)


def get_hk(**uargs):
    if uargs.get("wait",False):
        return wait(lambda :get_hk(**{**uargs, 'wait': False}))

    args=dict(
            rebin=0,
	    vetofiltermargin=0.02,
            ra=0,
            dec=0,
            t1=0,t2=0,
            burstfrom=0,burstto=0,
            greenwich="yes",
            )
    args.update(uargs)

    if args['target']=="VETO":
        args['target'] = "IBIS_VETO"

    if 'mode' in uargs:
        mode=uargs.pop("mode")
    else:
        mode="stats"


    s = "http://134.158.75.161/data/integral-hk/api/v1.0/%(target)s/%(utc)s/%(span).5lg/stats?" % args + \
        "rebin=%(rebin).5lg&ra=%(ra).5lg&dec=%(dec).5lg&burstfrom=%(t1).5lg&burstto=%(t2).5lg&vetofiltermargin=%(vetofiltermargin).5lg&greenwich=%(greenwich)s" % args
    print(s.replace("stats", "png"))

    if mode == "lc":
        s=s.replace("/stats","")

    if 'dry' in args and args['dry']:
        return

    if 'onlyprint' in args and args['onlyprint']:
        return

    r = requests.get(s,auth=auth)
    try:
        if r.status_code!=200:
            raise Exception("got %i ( != 200 ) HTTP response from service; response: %s"%(r.status_code, r.text))
        if mode == "lc":
            return np.genfromtxt(StringIO.StringIO(r.content))
        return r.json()
    except:
        print(r.content)
        raise ServiceException(r.content)


def get_cat(utc):
    s = "http://134.158.75.161/cat/grbcatalog/api/v1.1/" + utc
    print(s)
    r = requests.get(s,auth=auth)
    try:
        return r.json()
    except:
        raise ServiceException(r.content)


