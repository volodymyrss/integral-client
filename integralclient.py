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

def t2str(t):
    if isinstance(t,float):
        return "%.20lg"%t
    
    if isinstance(t,int):
        return "%i"%t

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
            ntries_left -= 1

            if ntries_left > 0:
                print("retrying timesystem",ntries_left,repr(e))
                time.sleep(5)
                continue
            else:
                raise
        
    

def data_analysis(name, modules, assume):
    c = requests.get("http://134.158.75.161/data/analysis/api/v1.0/" + name,
                     params=dict(modules=modules, assume=assume))
    try:
        return c.json()
    except:
        return c.content


def data_analysis_forget(jobkey):
    c = requests.get("http://134.158.75.161/data/analysis/api/v1.0/jobs/forget/" + jobkey)
    try:
        return c.json()
    except ServiceException as e:
        print(e)
        return c.content


def get_spimm_response(theta, phi, alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False, target="ACS",beta=-2.5,model="compton"):
    s = "http://134.158.75.161/integral/api/v1.0/spiresponse/direction/%.5lg/%.5lg?lt=%.5lg&model=%s&beta=%.5lg&ampl=%.5lg&alpha=%.5lg&epeak=%.5lg&emin=%.5lg&emax=%.5lg&emax_rate=%.5lg" % (
    theta, phi, lt, model, beta, ampl, alpha, epeak, emin, emax, emax_rate)

    if debug:
        print(s)
    r = requests.get(s,auth=auth)

    try:
        return r.json()
    except:
        print(r.content)

def get_response(theta, phi, radius=0.1, alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS",model="compton", width=1,beta=-2.5):
    #s = "http://134.158.75.161/integral/api/v1.0/response/direction/%.5lg/%.5lg?lt=%.5lg&model=compton&ampl=%.5lg&alpha=%.5lg&epeak=%.5lg&emin=%.5lg&emax=%.5lg&emax_rate=%.5lg" % (
    #theta, phi, lt, ampl, alpha, epeak, emin, emax, emax_rate)

    url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg&width=%(width).5lg"
   # url="http://localhost:5556/api/v1.0/"+target+"/response?lt=%(lt).5lg&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
    url+="&emin=%(emin).5lg"
    url += "&emax=%(emax).5lg"

    url = url % dict(
        lt=str(lt),
        theta=theta,
        phi=phi,
        radius=radius,
        alpha=alpha,
        epeak=epeak,
        model=model,
        beta=beta,
        width=width,
        ampl=ampl,
        emin=emin,
        emax=emax,
        emax_rate=emax_rate
    )

    #print(url)

    if debug:
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


def get_response_map(alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS",kind="response",model="compton",beta=-2.5):
    url="http://cdcihn/response/api/v1.0/"+target+"/response?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg"
    #url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg"
   # url="http://localhost:5556/api/v1.0/"+target+"/response?lt=%(lt).5lg&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
    url+="&emin=%(emin).5lg"
    url+="&emax=%(emax).5lg"
    url+="&emax_rate=%(emax_rate).5lg"
    
    lt=str(lt)

    url = url % dict(
        lt=lt,
        model=model,
        alpha=alpha,
        beta=beta,
        epeak=epeak,
        ampl=ampl,
        emin=emin,
        emax=emax,
        emax_rate=emax_rate
    )

    if debug:
        print(url)
    
    try:
        r = requests.get(url,auth=auth)
        r = r.json()
    except Exception as e:
        print("problem",e)
        print(r.text)
        raise

    return r[kind]


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

def get_hk_lc(target,utc,span,**uargs):
    args=dict(
            rebin=0,
            api="v1.0",
            )
    args.update(uargs)

    args['target']=target
    args['utc']=utc
    args['span']=span

    if args['target']=="VETO":
        args['target'] = "IBIS_VETO"
        raise ServiceException(r.content)

    print(args)

    s = "http://134.158.75.161/data/integral-hk/api/%(api)s/%(target)s/%(utc)s/%(span).5lg&rebin=%(rebin).5lg" % args 
    print(s)

    if 'dry' in args and args['dry']:
        return

    if 'onlyprint' in args and args['onlyprint']:
        return

    r = requests.get(s,auth=auth)
    if r.status_code==202:
        if find_exception(r.content) is None:
            try:
                c=r.json()
            except:
                c=r.content
            raise Waiting(s,c)
    if r.status_code!=200:
        raise ServiceException("bad status: %i"%r.status_code,r.content)
    return r

def get_hk(**uargs):
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
            raise
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


import time
def query_web_service(service,url,params={},wait=False,onlyurl=False,debug=False,json=False,test=False,kind="GET",data={}):
    s = "http://134.158.75.161/data/integral-hk/api/v2.0/"+service+"/" + url
    print(s)

    if debug:
        params=dict(params.items()+[('debug','yes')])

    if onlyurl:
        return s+"?"+urllib.urlencode(params)

    while True:
        if kind == "GET":
            r = requests.get(s,auth=auth,params=params)
        elif kind == "POST":
            r = requests.post(s,auth=auth,params=params,data=data)
        else:
            raise Exception("can not handle request: "+kind)
        
        find_exception(r.content)

        if test:
            print(r.status_code)
            return
            
       # print r.content
        if r.status_code==200:
            if debug:
                c=r.json()
                if c['result'] is not None:
                    c['result']=c['result'][:300]
                return c
            else:
                if json:
                    try:
                        return r.json()
                    except Exception as e:
                        print(e)#,r.content
                        raise
                else:
                    return r
        if not wait:
            try:
                c=r.json()
            except:
                c=r.content
            raise Waiting(s,c)
        time.sleep(1.)

