import pyfits
import numpy as np
from matplotlib import pylab as p
import healpy

class Response3D:

    def __init__(self, fn, influx):
        self.nside=16
        self.npx=healpy.nside2npix(self.nside)
        self.theta, self.phi = healpy.pix2ang(self.nside, np.arange(healpy.nside2npix(self.nside)))
        self.theta *= 180. / np.pi
        self.phi *= 180. / np.pi

        self.influx=influx

        self.f = pyfits.open(fn)

        self.e1 = self.f[1].data['EMIN']
        self.e2 = self.f[1].data['EMAX']
        self.ec = (self.e1 + self.e2) / 2.
        self.de = (self.e2 - self.e1)

    def get_map(self, energy, dlogenergy):
        men = abs(np.log10(self.ec / energy)) < dlogenergy

        print self.e2[men].max(), self.e1[men].min()

        frac = (10000 - 30) / (self.e2[men].max() - self.e1[men].min())

        print frac

        return self.f[0].data[:, men, 0].sum(1) / (self.influx * (6000 - 30) / self.npx / frac)

    def plot_vs_en(self,m):
        frac = sum(m)*1./m.shape[0]
        print "fraction:",frac


        effarea=self.f[0].data[m,:,0].sum(0)  / (self.influx * self.de*frac)
        p.plot(self.e1,effarea)

class MassModel:
    def __init__(self,root):
        self.root=root
        self.inevents = int(open(self.root+"/summary.txt").read().split()[-1])
        self.influx = self.inevents / (400 ** 2 * np.pi * 2) / (6000 - 30)


        self.ISGRIr3d = Response3D(self.root+"/response_isgri_3d.fits",self.influx)
        self.PICsITr3d = Response3D(self.root+"/response_picsit_3d.fits",self.influx)
        self.ACSr3d = Response3D(self.root+"/response_spiacs_3d.fits",self.influx)
        self.VETOr3d = Response3D(self.root+"/response_ibisveto_3d.fits",self.influx)


    def plot_maps(s):
        acsmp_timm = s.ACSr3d.get_map(100, 0.5)
        vetomp = s.VETOr3d.get_map(100, 0.5)
        picsitmp = s.PICsITr3d.get_map(100, 0.5)
        isgrimp = s.ISGRIr3d.get_map(100, 0.5)

        def plot(v, (vmin, vmax), title):
            rot = (180, 0, 180)
            # rot=(180,90,180)

            fig = p.figure(figsize=(15, 10))
            healpy.mollview(v, min=v.min(), max=v.max(), rot=rot, title=title, cmap="YlOrBr", fig=fig.number)
            # healpy.mollview(v,min=vmin,max=vmax,rot=rot,title=title,cmap="YlOrBr",fig=fig.number)
            healpy.graticule()

            # savefig("/home/vsavchenko/drafts/ligo/performance/"+title.replace(" ","_").replace("/","_")+"_model.png")

        # rot=(180,90,180)

        # healpy.mollview(mp/(influx*(6000-30)/npx/frac),min=2000,max=7000,rot=(0,0,180))
        # healpy.mollview(f[0].data[:,men,0].sum(1)/(influx*(6000-30)/npx/frac)/factor,min=2000,max=9000,rot=rot,title="SPI-ACS TIMM")
        # healpy.graticule()

        plot(acsmp_timm, (2000, 9000), "SPI-ACS TIMM")
        plot(picsitmp, (2000, 9000), "PICsIT TIMM")
        plot(isgrimp, (2000, 9000), "ISGRI TIMM")
        #plot(acsmp, (2000, 9000), "ACS SPIMM")
        plot(vetomp, (1000, 4000), "IBIS_VETO TIMM")

        # m_vetoadv=(fv[0].data[:,men,0].sum(1)/f[0].data[:,men,0].sum(1))>0.7

        plot(vetomp / acsmp_timm, (0.5, 2), title="IBIS_VETO/SPI-ACS TIMM")
        #plot(vetomp / acsmp, (0.5, 2), "IBIS_VETO/SPI-ACS SPIMM")

    def plot_vs_en(self):
        self.ACSr3d.plot_vs_en()
