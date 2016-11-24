import json

class ServiceException(Exception):
    def __str__(self):
        try:
            return json.dumps(("ERROR",self.__class__.__name__,self.args))
        except:
            return json.dumps(("ERROR",self.__class__.__name__,repr(self.args)))
        

def find_exception(r):
    if isinstance(r,str):
        content=r
        status=200
    else:
        content=r.content
        status=r.status_code

    try:
        js=json.loads(content)
        marker=js[0]
        name=js[1]
        comment=js[2]
    except: # ValueError:
        return

    
    if marker=="ERROR":
        subcs=[subc for subc in ServiceException.__subclasses__() if name==subc.__name__]
        if subcs==[]:
            raise ServiceException("undefined service exception: "+content)
        raise subcs[0]("requested service exception: ",comment)
    

class NoLiveServices(ServiceException):
    pass

class Dependency(ServiceException):
    pass
