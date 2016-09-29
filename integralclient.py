import requests
import StringIO
from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np

integral_services_server="134.158.75.161"

def get_acs_effarea(theta,phi,lt=100):
    return loadtxt(StringIO.StringIO(requests.get("http://localhost:5555/api/v1.0/effarea/direction/%.5lg/%.5lg?lt=%.5lg"%(theta,phi,lt)).content))

def converttime(informat,intime,outformat):
    return requests.get('http://'+integral_services_server+'/integral/integral-timesystem/api/v1.0/'+informat+'/'+intime+'/'+outformat).content

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
    except Exception as e:
        print e
        return c.content


def get_spimm_response(theta, phi, alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False):
    s = "http://134.158.75.161/integral/api/v1.0/spiresponse/direction/%.5lg/%.5lg?lt=%.5lg&model=compton&ampl=%.5lg&alpha=%.5lg&epeak=%.5lg&emin=%.5lg&emax=%.5lg&emax_rate=%.5lg" % (
    theta, phi, lt, ampl, alpha, epeak, emin, emax, emax_rate)

    if debug:
        print s
    r = requests.get(s)

    try:
        return r.json()
    except:
        print r.content

def get_response(theta, phi, radius=0.1, alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS"):
    #s = "http://134.158.75.161/integral/api/v1.0/response/direction/%.5lg/%.5lg?lt=%.5lg&model=compton&ampl=%.5lg&alpha=%.5lg&epeak=%.5lg&emin=%.5lg&emax=%.5lg&emax_rate=%.5lg" % (
    #theta, phi, lt, ampl, alpha, epeak, emin, emax, emax_rate)

    url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
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
        ampl=ampl,
        emin=emin,
        emax=emax,
        emax_rate=emax_rate
    )

    #print(url)

    if debug:
        print url
    r = requests.get(url)

    try:
        r=r.json()

        return {'flux':r['enflux'],'phflux':r['phflux'],'response':np.mean(r['response']),'rate':np.mean(r['rate']),'rate_min':np.min(r['rate']),'rate_min':np.max(r['rate'])}
    except Exception as e:
        raise
        print r.content


def get_response_map(alpha=-1, epeak=600, emin=75, emax=2000, emax_rate=20000, lt=75, ampl=1, debug=False,target="ACS",kind="response"):
    url="http://134.158.75.161/data/response/api/v1.0/"+target+"?lt=%(lt)s&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
   # url="http://localhost:5556/api/v1.0/"+target+"/response?lt=%(lt).5lg&theta=%(theta).5lg&phi=%(phi).5lg&radius=%(radius).5lg&mode=all&epeak=%(epeak).5lg&alpha=%(alpha).5lg&ampl=%(ampl).5lg"
    url+="&emin=%(emin).5lg"
    url+="&emax=%(emax).5lg"
    
    lt=str(lt)

    url = url % dict(
        lt=lt,
        alpha=alpha,
        epeak=epeak,
        ampl=ampl,
        emin=emin,
        emax=emax,
        emax_rate=emax_rate
    )

    if debug:
        print url
    r = requests.get(url).json()

    return r[kind]


def get_sc(utc, ra=0, dec=0, debug=False):
    s = "http://134.158.75.161/integral/integral-sc-system/api/v1.0/" + utc + "/%.5lg/%.5lg" % (ra, dec)
    if debug:
        print s
    r = requests.get(s)
    try:
        return r.json()
    except:
        print r.content


def get_hk(**uargs):
    args=dict(
            rebin=0
            )
    args.update(uargs)

    if args['target']=="VETO":
        args['target'] = "IBIS_VETO"


    s = "http://134.158.75.161/data/integral-hk/api/v1.0/%(target)s/%(utc)s/%(span).5lg/stats?" % args + \
        "rebin=%(rebin).5lg&ra=%(ra).5lg&dec=%(dec).5lg&burstfrom=%(t1).5lg&burstto=%(t2).5lg" % args
    print s.replace("stats", "png")

    if 'dry' in args and args['dry']:
        return

    if 'onlyprint' in args and args['onlyprint']:
        return

    r = requests.get(s)
    try:
        return r.json()
    except:
        print r.content


def get_cat(utc):
    s = "http://134.158.75.161/cat/grbcatalog/api/v1.1/" + utc
    print s
    r = requests.get(s)
    try:
        return r.json()
    except:
        print r.content


        # print get_response(theta=90,phi=360-50,alpha=-0.4,epeak=3000,emin=10,emax=1000,lt=100, ampl=0.1)


