from numpy import *

import healpy
import requests
from collections import defaultdict

import sys
import os
#sys.path.append("/home/vsavchenko/work/projects/integral/integralclient")
from integralclient import *
import integralclient
import transient
reload(integralclient)

import json

## vetogood=loadtxt("apcclwn12.sshfs//Integral/throng/savchenk/projects/integral/offgrb/ibisveto_sig_names.txt",dtype="|S")
#vetogood[:,4]

txttable_filename="/Integral/throng/savchenk/projects/integral/offgrb/gbmtable.txt"
#txttable_filename="apcclwn12.sshfs/Integral/throng/savchenk/projects/integral/offgrb/gbmtable_short.txt"
fieldsline=4

fields=[a.strip() for a in open(txttable_filename).readlines()[fieldsline].split("|")[1:-1]]
#print "found fields:",fields

bursts=[dict(zip(fields,l.split("|")[1:-1])) for l in open(txttable_filename).readlines()[fieldsline+1:] if len(l.split("|"))==len(fields)+2]
bursts=sorted(bursts,key=lambda x:x['name'])

print len(bursts)
cresults=[]

import time
reload(integralclient)
reload(transient)
#for r in completeresults[:100]:

Tlist=[]

t0=time.time()
n=0

def sfloat(x):
    try:
        return float(x)
    except:
        return 0
    
for burst in sorted(bursts,key=lambda b:-sfloat(b['fluence'])):
   # if burst['name']!="GRB081012045": continue
    
   # if float(burst['t90'])>2: continue
    T=transient.Transient(gbm=burst)    
#
    T.filter=lambda s:True

    
    if T.load("offgrb"): # and False:
        try:
            #print T.ijd
            print T.acs['lc'][u'burst counts']
            print T.veto['lc'][u'burst counts']
            

            Tlist.append(T)
            
        except Exception as e:
            print e
           # raise
            continue

        #T.get_rates()
        #T.save()
        
        continue
  

    try:
        T.import_gbm(burst)     
    except Exception as e:
        #raise
        print "import failed:",T.exceptions,e
    
    n+=1
    print (time.time()-t0)/n
    
    del T.filter
    T.save()
   # break
    
#T.sc

