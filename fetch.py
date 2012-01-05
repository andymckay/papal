import os
from datetime import datetime, timedelta

servers = ['http_app_addons', 'http_app_addons_appspreviewdev',
           'http_app_addons_appspreview']
for server in servers:
    for k in range(14, 0, -1):
        day = (datetime.today() - timedelta(days=k))

        cmd = open(os.path.expanduser('~/.paypal_logs')).read()
        data = {'server': server, 'date': day.strftime('%Y-%m-%d'),
                'year': day.strftime('%Y'),
                'month': day.strftime('%m')}
        print 'Executing: %(server)s for %(date)s' % data
        print cmd % data
        os.system(cmd % data)
