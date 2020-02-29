import datetime as dt


def year(request):
    now = dt.datetime.today().year
     
    return {'year': now}