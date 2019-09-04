

def test_time():
    import integralclient as ic

    assert ic.converttime("IJD",2000,"UTC") == "2005-06-22T23:58:55.816"

    assert ic.converttime("IJD",2000,"SCWID") == "032800550010"

def test_sc():
    import integralclient as ic
    import random
    assert 'barytime' in ic.get_sc("%.10lg"%random.uniform(2000,7000))

def test_response():
    import integralclient as ic
    r = ic.get_response_map()
    assert len(r) > 100

    print(r)
    
    r = ic.get_response(0,0)
    print(r)

def test_gethk():
    import integralclient as ic
    import random

    ijd = list(map(float, ic.converttime("SCWID","%.4i00410010"%random.randint(100,2000),"IJD").split(":")))
    print("ijd",ijd)

    
    lc = ic.get_hk(target="ACS", utc=ijd[0],  span=300, wait=True)

    print(lc)
    
    assert 'count limit 3 sigma' in lc['lc']
    assert 'excvar' in lc['lc']
    assert 'maxsig' in lc['lc']

    assert lc['lc']['excvar'] < 1.5
    assert lc['lc']['excvar'] > 0.8

def test_gethk_binevents():
    import integralclient as ic
    import random

    ijd = list(map(float, ic.converttime("SCWID","%.4i00410010"%random.randint(100,2000),"IJD").split(":")))
    print("ijd",ijd)

    
    lc = ic.get_hk(target="isgri", utc=ijd[0] + 1000./3600./24,  span=300, wait=True)

    print(lc)

    assert 'count limit 3 sigma' in lc['lc']
    assert 'excvar' in lc['lc']
    assert 'maxsig' in lc['lc']

    assert lc['lc']['excvar'] < 1.5
    assert lc['lc']['excvar'] > 0.8
