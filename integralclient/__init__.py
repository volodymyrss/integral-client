from __future__ import print_function

import requests
import urllib
import time
from io import StringIO
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np
import os
from .service_exception import *
import io
import logging

logging.basicConfig()

import click

@click.group()
def cli():
    pass

def get_auth():
    for n, mu, m in [
                    ("env", 
                        lambda:"integral",
                        lambda:os.environ.get("K8S_SECRET_INTEGRAL_CLIENT_SECRET")),
                    ("homefile", 
                        lambda:open(os.environ['HOME']+"/.secret-client-user").read().strip(),
                        lambda:open(os.environ['HOME']+"/.secret-client").read().strip(),
                        )
                ]:
        try:
            return requests.auth.HTTPBasicAuth(mu(), m())
        except:
            print("failed with", n)

auth=get_auth()

#integral_services_server="134.158.75.161"

def detect_gw_endpoint():
    #https://www.astro.unige.ch/cdci/astrooda/dispatch-data/gw/timesystem/api/v1.0/converttime/UTC/2009-11-11T11:11:11/REVNUM

    for endpoint in [
 #       "http://cdcihn/timesystem",
        "https://www.astro.unige.ch/cdci/astrooda/dispatch-data/gw/",
                ]:
        try:
            r = requests.get(endpoint+"/timesystem/api/v1.0/converttime/UTC/2009-11-11T11:11:11/REVNUM")
            if r.status_code == 200:
                logging.info("selecting timesystem endpoint %s", endpoint)
                return endpoint
            logging.info("failed to fetch endpoint %s response %s %s", endpoint, r, r.text)
        except Exception as e:
            logging.info("failed to fetch endpoint %s exception %s", endpoint, e)

    raise Exception("no suitable gw endpoint")
    

gw_endpoint = detect_gw_endpoint()


def wait(f,timeout=5,ntries=30):
    ntries_left = ntries
    while ntries_left > 0:
        try:
            return f()
        except Exception as e: # or service?
            logging.info("service exception %s tries left %i", repr(e),  ntries_left)
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
    url=gw_endpoint+'/timesystem/api/v1.0/scwlist/'+dr+'/'+t2str(t1)+'/'+t2str(t2)

    #url='https://analyse.reproducible.online/timesystem/api/v1.0/converttime/IJD/4000/SCWID'

    if debug:
        logging.info("url %s",url)

    ntries_left = 30

    while ntries_left > 0:
        try:
            r=requests.get(url)

            if r.status_code!=200:
                raise ServiceException('error converting '+url+'; from timesystem server: '+str(r.text))

            try:
                return r.json()
            except:
                if debug:
                    logging.info("got string %s", r.text)
                return r.text.strip(r"\n").strip("\"")

        except Exception as e:
            ntries_left -= 1

            if ntries_left > 0:
                logging.info("retrying timesystem %i %s",ntries_left,repr(e))
                time.sleep(5)
                continue
            else:
                raise

@cli.command("converttime")
@click.argument("informat")
@click.argument("intime")
@click.argument("outformat")
@click.option("-d", "--debug", is_flag=True)
@click.option("-j", default=False, is_flag=True)
def _converttime(informat, intime, outformat, debug=True, j=False):
    r = converttime(informat,intime,outformat, debug=debug)

    if j:
        print(json.dumps(r))
    else:
        click.echo(r)
    

def converttime(informat, intime, outformat, debug=True):
    if intime == "now":
        informat="UTC"
        intime=time.strftime("%Y-%m-%dT%H:%M:%S")

    #url='http://'+integral_services_server+'/integral/integral-timesystem/api/v1.0/'+informat+'/'+intime+'/'+outformat
    url=gw_endpoint+'/timesystem/api/v1.0/converttime/'+informat+'/'+t2str(intime)+'/'+outformat
    #url='https://analyse.reproducible.online/timesystem/api/v1.0/converttime/IJD/4000/SCWID'


    if debug:
        logging.info("url %s",url)

    ntries_left = 30

    while ntries_left > 0:
        try:
            r=requests.get(url)

            if r.status_code!=200:
                raise ServiceException('error converting '+url+'; from timesystem server: '+str(r.text))

            if outformat=="ANY":
                try:
                    return r.json()
                except:
                    pass
            return r.text.strip().strip("\"")

        except Exception as e:
            if 'is close' in repr(e):
                raise
                
            ntries_left -= 1

            if ntries_left > 0:
                logging.info("retrying timesystem %i %s",ntries_left,repr(e))
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


    url="http://cdcihn/response/api/v1.0/%(target)s/response?lt=%(lt)s&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg&width=%(width).5lg"
    url+="&emin=%(emin).5lg"
    url += "&emax=%(emax).5lg"

    url = url % kwargs

    logging.info(url)

    r = requests.get(url)

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
        raise ServiceException("problem with service: "+repr(e)+"; "+repr(r)+" "+getattr(r,'text',"?"))


def get_response_map(**kwargs):
    if kwargs.get('wait', True):
        return wait(lambda :get_response_map(**{**kwargs, 'wait':False}))

    default_kwargs = dict(alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS",kind="response",model="compton",beta=-2.5)

    kwargs = {**default_kwargs, **kwargs}
    kwargs['lt'] = str(kwargs['lt'])

    url="http://cdcihn/response/api/v1.0/%(target)s/response?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg&model=%(model)s&beta=%(beta).5lg"
    url+="&emin=%(emin).5lg"
    url+="&emax=%(emax).5lg"
    url+="&emax_rate=%(emax_rate).5lg"
    

    url = url % kwargs
    logging.info(url)
    
    try:
        r = requests.get(url)
        r = r.json()
    except Exception as e:
        logging.info("problem %s",e)
        logging.info(r.text)
        raise

    return r[kwargs['kind']]


def get_sc(utc, ra=0, dec=0, debug=False):
    s = "http://cdcihn/scsystem/api/v1.0/sc/" + utc + "/%.5lg/%.5lg" % (ra, dec)
    if debug:
        logging.info(s)
    r = requests.get(s,timeout=300)
    try:
        return r.json()
    except Exception as e:
        logging.info(r.content)
        raise ServiceException(e,r.content)

enableODA = False

if enableODA:
    try:
        import oda

        def get_hk_binevents(**uargs):
            t0_utc = converttime("ANY", uargs['utc'], "UTC")

            r = oda.evaluate("odahub","integral-multidetector","binevents",
                         t0_utc=t0_utc,
                         span_s=uargs['span'],
                         tbin_s=max(uargs['rebin'], 0.01),
                         instrument=uargs['target'].lower(),
                         emin=uargs['emin'],
                         emax=uargs['emax'])

            logging.info(r.keys())

            c = np.array(r['lc']['counts'])
            m = c > np.quantile(c, 0.1)

            r['lc']['count limit 3 sigma'] = np.std( c[m] )  * 3
            r['lc']['excvar'] = np.std( c[m] ) / np.mean(c[m])**0.5
            r['lc']['maxsig'] = np.max( (c[m] - np.mean(c[m]))/c[m]**0.5) / r['lc']['excvar']

            return r

    #        return r['lc']
    except Exception as e:
        logging.info("failed to import oda")


def get_hk(**uargs):
    if uargs.get("wait",False):
        return wait(lambda :get_hk(**{**uargs, 'wait': False}))

    debug=uargs.pop("debug", False)

    args=dict(
            rebin=1,
            vetofiltermargin=0.02,
            ra=0,
            dec=0,
            t1=0,t2=0,
            burstfrom=0,burstto=0,
            greenwich="yes",
            emin=25,
            emax=80,
            )
    args.update(uargs)

    if args['target']=="VETO":
        args['target'] = "IBIS_VETO"

    if args['target'].upper() in ["ISGRI", "SPI"]:
        return get_hk_binevents(**args)

    if 'mode' in uargs:
        mode=uargs.pop("mode")
    else:
        mode="stats"


    s = "http://lal.odahub.io/data/integral-hk/api/v1.0/%(target)s/%(utc)s/%(span).5lg/stats?" % args + \
        "rebin=%(rebin).5lg&ra=%(ra).5lg&dec=%(dec).5lg&burstfrom=%(t1).5lg&burstto=%(t2).5lg&vetofiltermargin=%(vetofiltermargin).5lg&greenwich=%(greenwich)s" % args

    logging.info(s.replace("stats", "png"))

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
            return np.genfromtxt(io.StringIO(r.text))
        return r.json()
    except:
        logging.info(r.content)
        raise ServiceException(r.content)


def get_hk_genlc(target, t0, dt_s, debug=False):
    url = gw_endpoint+"/integralhk/api/v1.0/genlc/%s/%.20lg/%.10lg"%(target, t0, dt_s)

    r = requests.get(url)

    print(url)

    text = r.text.strip().strip("\"").replace("\\n","\n")

    if debug:
        print(text)

    try:
        d = np.genfromtxt(io.StringIO(text), skip_header=5, names=("t_ijd", "t_rel", "counts", "t_since_midnight") )
    except:
        print(text)
        raise

    return d

def get_cat(utc):
    s = "http://{}/cat/grbcatalog/api/v1.1/" + utc
    logging.info(s)
    r = requests.get(s,auth=auth)
    try:
        return r.json()
    except:
        raise ServiceException(r.content)


if __name__ == "__main__":
    cli()
