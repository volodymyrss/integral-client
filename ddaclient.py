a = []
b = []
ae = []
be = []
theta = []
phi = []

results = []
completeresults = []

ntotal = 0

bystatus = defaultdict(int)
for burst in bursts:
    n = burst['name']
    ntotal += 1

    print bystatus, ntotal, len(results)

    r = data_analysis(
        "FluenceForBurst",
        modules='ddosa,/scsystem/P1.3,/plot/P1,/burst/P1.1,/integraltime/v1.1,/spiacs/P1.10,/synthetic/P1.4,/offgrb/P1.21',
        assume='offgrb.Burst(use_b=offgrb.PickNamed(input_name="' + n + '")),offgrb.FluenceForBurst(use_respsuffix="_lt106")'
    )
    rpl = data_analysis(
        "PlotLC",
        modules='ddosa,/scsystem/P1.3,/plot/P1,/burst/P1.1,/integraltime/v1.1,/spiacs/P1.10,/synthetic/P1.4,/offgrb/P1.21',
        assume='offgrb.Burst(use_b=offgrb.PickNamed(input_name="' + n + '"),use_a=11)'
    )
    # r['alljobs']=""

    try:
        a = dict([(a, b) for a, b in r.items() if a not in ['result', 'alljobs']])
    except:
        print r
        raise

    try:
        a = dict([(a, b) for a, b in rpl.items() if a not in ['result', 'alljobs']])
    except:
        # print rpl
        raise

    bystatus[r['status']] += 1
    bystatus[rpl['status']] += 1

    #  print
    #  print
    #  print "FLUENCE"

    if 'result' in r:
        if r['result'] == "all failed...":
            #         print r
            print "forgetting returns", data_analysis_forget(r['jobkey'])
            bystatus['restarted'] += 1
            continue

        try:
            #       print r['result']['d']['flux_75_2000']/1e-10
            flux_75_2000 = r['result']['d']['flux_75_2000']
            t90 = r['result']['d']['t90']
            tspec = r['result']['d']['tspec']

            #      print "ok"
        except Exception as e:
            #       print e
            continue
    else:
        if r['status'] in ["finished", "failed"]:
            #      print r
            print "forgetting returns", data_analysis_forget(r['jobkey'])
            bystatus['restarted'] += 1
            continue

            #   print "no fluence result",r['status']
        continue
        # if 'result' in r:
        #    print r['result']['d']['flux_75_2000']/1e-10


        #  print
        #  print "BURST"

    if 'result' in rpl:
        if rpl['result'] == "all failed...":
            #        print rpl
            print "forgetting returns", data_analysis_forget(rpl['jobkey'])
            bystatus['restarted'] += 1
            continue

        if 'summary' not in rpl['result']:
            #       print "no summary",rpl['result']
            continue

        if isnan(rpl['result']['summary']['IBISVETOBurst']['total_sigma']): continue
        if isnan(rpl['result']['summary']['ACSBurst']['total_sigma']): continue
        t0_ijd = rpl['result']['summary']['ACSBurst']['t0_ijd']

        veto_total_counts = rpl['result']['summary']['IBISVETOBurst']['total_counts']
        acs_total_counts = rpl['result']['summary']['ACSBurst']['total_counts']
        veto_total_sigma = rpl['result']['summary']['IBISVETOBurst']['total_sigma']
        acs_total_sigma = rpl['result']['summary']['ACSBurst']['total_sigma']
        theta = rpl['result']['summary']['orientation']['theta']
        phi = rpl['result']['summary']['orientation']['phi']

        #  print "ok"
    else:
        if rpl['status'] in ["finished", "failed"]:
            #       print rpl
            print "forgetting returns", data_analysis_forget(rpl['jobkey'])
            bystatus['restarted'] += 1
            continue

        print "no burst result", rpl['status']
        continue


        # if veto_total_counts<=0: continue

    link = "http://134.158.75.161/data/integral-hk/api/v1.0/ACS/%.20lg/500/png?theta=%.5lg&phi=%.5lg&rebin=8" % (
    t0_ijd, theta, phi)
    link2 = "http://134.158.75.161/data/integral-hk/api/v1.0/IBIS_VETO/%.20lg/500/png?theta=%.5lg&phi=%.5lg" % (
    t0_ijd, theta, phi)

    results.append(
        [flux_75_2000, acs_total_counts, veto_total_counts, theta, phi, tspec, acs_total_sigma, veto_total_sigma, n,
         t0_ijd, link, link2])
    completeresults.append([r, rpl])

print bystatus, ntotal, len(results)

