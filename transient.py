from __future__ import print_function

from integralclient import *
import cPickle as pickle


import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u
import json

def store_exceptions(f):
    def nf(self):
        try:
            return f(self)
        except Exception as e:
            self.exceptions.append(e)
            raise

    return nf

class Transient(object):
    exceptions=[]

    def __init__(self,gbm=None):
        self.gbm=gbm

    def load(self,storeroot="offgrb"):
        fn = storeroot+"/%s.json" % self.gbm['name']
        try:
            c = pickle.load(open(fn))
            for a,b in c.items():
                #print(a)
                setattr(self,a,b)

            print("loaded", fn)
            return True
        except Exception as e:
            print(e)
            return False

    def save(self):
        fn = "offgrb/%s.json" % self.gbm['name']
        pickle.dump(self.__dict__, open(fn, "w"))

    def compute_fluxes(s):
        s.fluxes={}
        s.model_rates= {}

        rd=dict(
            theta=s.sc['theta'], 
            phi=s.sc['phi'],
            alpha=s.alpha, 
            epeak=s.epeak,
            debug=True,
            ampl=s.ampl
        )

        for target in ["ACS","VETO"]:
            for lt in [75,100,150]:
                s.model_rates[(target,lt)]=get_response(emin=75, emax=2000, lt=lt, emax_rate=6000, target=target, **rd)

        for e1,e2 in [(10,1000), (75,2000)]:
            s.fluxes[(e1,e2)] = get_response(emin=e1,emax=e2,lt=-2, emax_rate=6000,**rd)


        if False:
            s.acs_ranges = []
            s.fluences = []
            for x_alpha in s.alpha - s.alpha_neg_err, s.alpha + s.alpha_pos_err:
                for x_epeak in s.epeak - s.epeak_neg_err, s.epeak + s.epeak_pos_err:
                    for x_ampl in s.ampl - s.ampl_neg_err, s.ampl + s.ampl_pos_err:
                        gr = get_response(theta=s.sc['theta'], phi=s.sc['phi'], alpha=x_alpha, epeak=x_epeak, emin=75,
                                          emax=2000,
                                          lt=100, ampl=x_ampl)
                        s.acs_ranges.append(gr['acsrate'] * (s.dt2 - s.dt1))
                        s.fluences.append(gr['flux'] * (s.dt2 - s.dt1))
                        print("acs", s.acs_ranges[-1], "fluence", s.fluences[-1])

            min(s.acs_ranges), max(s.acs_ranges)
        
    def converttime(s):
        s.ijd=converttime("UTC",s.utc,"IJD")

    rates2load=["ACS","VETO"]

    def get_rates(s,onlyprint=False):
        for target in s.rates2load:
            setattr(s,target,get_hk(target=target, utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec,onlyprint=onlyprint))

        #s.VETO = get_hk(target="IBIS_VETO", utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec,onlyprint=onlyprint)
        #s.PICsIT = get_hk(target="SPTI1234", utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec,onlyprint=onlyprint)
        #s.ISGRI = get_hk(target="ISGRI", utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec,onlyprint=onlyprint)
        #s.Compton = get_hk(target="Compton", utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec,onlyprint=onlyprint)
        s#.SPI = get_hk(target="SPI", utc=s.utc, t1=s.dt1, t2=s.dt2, ra=s.ra, dec=s.dec, onlyprint=onlyprint)

    def make_sens(self):
        self.compute_flux(10, 1000)
        self.compute_flux(75, 2000)

        for kind in ['ACS','VETO']: #,'PIC','isgri','compton']:
            try:
                bc=getattr(self,kind)['lc']['burst counts']
                berr = getattr(self, kind)['lc']['burst counts error']
                bkg = getattr(self, kind)['lc']['mean bkg']
                stdbkg = getattr(self, kind)['lc']['std bkg']
            except:
                print("no data for",kind)
                continue

            for (e1,e2) in [(10,1000),(75,2000)]:
                r=self.fluxes[(e1, e2)]['flux'] / bc * self.dt_eff_alt

                print(kind,"response %.5lg - %.5lg"%(e1,e2),"SIG",bc/berr,r,"error",bc*r,"bkg std",stdbkg*r,bkg**0.5*r)

    searchcat=False

    #@store_exceptions
    def import_gbm(s,burst):
        s.gbm=burst
        s.utc = burst['trigger_time'].replace(" ", "T").strip()

        print(s.utc)

        s.converttime()

        try:
            s.fluence = float(burst['fluence'])
            s.dt1 = float(burst['flnc_spectrum_start'])
            s.dt2 = float(burst['flnc_spectrum_stop'])
        except:
            print("issue in GBM table"),burst['fluence'],burst['flnc_spectrum_start']
            return

        s.fluence_spec = float(burst['flnc_comp_ergflnc'])
        s.fluence_spec_error = float(burst['flnc_comp_ergflnc_error'])
        s.flux_spec = float(burst['flnc_comp_ergflux'])
        s.fluence = float(burst['fluence'])
        s.fluence_error = float(burst['fluence_error'])
        s.t90 = float(burst['t90'])

        s.alpha = float(burst['flnc_comp_index'])
        s.alpha_pos_err = float(burst['flnc_comp_index_pos_err'])
        s.alpha_neg_err = float(burst['flnc_comp_index_neg_err'])
        s.epeak = float(burst['flnc_comp_epeak'])
        s.epeak_pos_err = float(burst['flnc_comp_epeak_pos_err'])
        s.epeak_neg_err = float(burst['flnc_comp_epeak_neg_err'])
        s.ampl = float(burst['flnc_comp_ampl'])
        s.ampl_pos_err = float(burst['flnc_comp_ampl_pos_err'])
        s.ampl_neg_err = float(burst['flnc_comp_ampl_neg_err'])


        print("diff", abs(s.flux_spec * (s.dt2 - s.dt1) - s.fluence) / s.fluence)


        c = SkyCoord(burst['ra'], burst['dec'], unit=(u.hourangle, u.deg))
        s.ra, s.dec, s.locerr= c.ra.deg, c.dec.deg,burst['error_radius']

        print("BURST", s.utc, s.dt1, s.dt2, s.ra, s.dec)
        print(s.utc, s.fluence, s.t90)
        print("model compton", s.alpha, s.ampl, s.epeak)
        
        s.sc = get_sc(s.utc, s.ra, s.dec, True)
        print("orientation", s.sc['theta'], s.sc['phi'])
        
        # print alpha,epeak,ampl

        s.dt=s.dt2-s.dt1
        s.dt_eff = s.fluence_spec / s.flux_spec
        s.dt_eff_alt=s.fluence/s.flux_spec
        
        print("times","t90:",s.t90, "dt" ,s.dt, "dt_eff:", s.dt_eff, "t_eff_alt",s.dt_eff_alt)
        print("fluence 10-1000", s.flux_spec * (s.dt2 - s.dt1), s.flux_spec * (s.dt2 - s.dt1),"table:", s.fluence, s.fluence_spec)
        #print("fluence 20-10000", s.acsresp_20_10000['flux'] * (dt2 - dt1))
        print("fluence error", s.fluence_error / s.fluence, s.fluence_spec_error / s.fluence_spec)

        print("orientation", s.sc['theta'], s.sc['phi'], s.locerr)
        s.theta,s.phi=s.sc['theta'], s.sc['phi']

        if s.searchcat:
            s.cat = get_cat(s.utc)
            print("location", s.ra, s.dec, s.cat['ra'], s.cat['dec'], "+/-", s.cat['locerr'])
        else:
            print("location", s.ra, s.dec)

        if s.filter(s):
            s.run()
            return True
        return False

    def run(s):
        s.compute_fluxes()
        s.get_rates()
        s.get_prediction()

        # print acsresp_75_2000
        # print acsresp_75_4700

    def get_prediction(s):
        for target in ["ACS","VETO"]:
            print("predictions ",target,":")

            try:
                burst_counts = getattr(s, target)['lc']['burst counts']
                burst_counts_err = getattr(s, target)['lc']['burst counts error']
            except Exception as e:
                s.exceptions.append(e)
                print("failed counts!")
                return


            #s.deadtime_av_model = (s.acsresp_75_2000['acsrate']+s.acs['lc']['mean bkg']) / (1.1e5 * 20)
            #s.deadtime_av = (s.acs['lc']['burst counts']/s.t90 +s.acs['lc']['mean bkg'])/ (1.1e5 * 20)
            #s.deadtime_max = (s.acs['lc']['maxcounts']+s.acs['lc']['mean bkg']) / (1.1e5 * 20)

            #print("dead time", s.deadtime_av,s.deadtime_av_model,s.deadtime_max)
            print("model conversion", "75:",s.model_rates[(target,75)]['response'],"100:",s.model_rates[(target,100)]['response'])
            print("real conversion", s.fluxes[(75,2000)]['flux'] * s.dt_eff / burst_counts)

            print("std burst counts",s.model_rates[(target,75)]['rate']*s.dt_eff,burst_counts),"+/-",burst_counts_err/burst_counts
            #print("eff burst counts bias", s.burst_counts / (s.acsresp_75_2000['acsrate'] * s.dt_eff),s.burst_counts / (s.acsresp_75_2000_150['acsrate'] * s.dt_eff))
            #print("efa burst counts bias", s.burst_counts / (s.acsresp_75_2000['acsrate'] * s.dt_eff_alt),s.burst_counts / (s.acsresp_75_2000_150['acsrate'] * s.dt_eff_alt))
            #print("t90 burst counts bias", s.burst_counts / (s.acsresp_75_2000['acsrate'] * s.t90),s.burst_counts / (s.acsresp_75_2000_150['acsrate'] * s.t90))
            #print(" dt burst counts bias", s.burst_counts / (s.acsresp_75_2000['acsrate'] * s.dt),s.burst_counts / (s.acsresp_75_2000_150['acsrate'] * s.dt))



