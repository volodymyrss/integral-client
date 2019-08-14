

def test_time():
    import integralclient as ic

    assert ic.converttime("IJD",2000,"UTC") == "2005-06-22T23:58:55.816"

    assert ic.converttime("IJD",2000,"SCWID") == "032800550010"

    assert 'barytime' in ic.get_sc("3000")
