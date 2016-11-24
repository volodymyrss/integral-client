import integralclient as ic
from service_exception import *

try:
    c=ic.query_web_service("integral-dumplc","api/v1.0/ACS/2016-11-23T13:34:37.51/602")
except ic.Waiting as e:
    print e.args[1]['key']
