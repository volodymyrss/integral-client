

def test_time():
    import integralclient as ic

    assert ic.converttime("IJD",2000,"UTC") == "2005-06-22T23:58:55.816"

    assert ic.converttime("IJD",2000,"SCWID") == "032800550010"

def test_sc():
    import integralclient as ic
    assert 'barytime' in ic.get_sc("3000")

def test_response():
    import integralclient as ic
    assert len(ic.get_response_map()) > 100

def test_gethk():
    import integralclient as ic
    ic.get_hk(target="ACS", utc = "2005-06-22T23:58:55.816",  span=300)
