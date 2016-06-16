#!/usr/bin/python3
import subprocess
import tarfile

from charms.reactive import when_not
from charms.reactive import set_state

from charmhelpers.core import hookenv
from charmhelpers.core.host import chdir
from charmhelpers.core.host import chownr
from charmhelpers.contrib.python.packages import pip_install

from charms.layer.whelp import Whelp, WHELP_HOME

from nginxlib import configure_site


config = hookenv.config()

    
@when_not('whelp.installed')
def install_whelp(self):
    '''
    Reactive hook to install whelp
    '''
    hookenv.status_set('maintenance', 'Installing whelp')

    whelp = Whelp()
    
    whelp_tar = hookenv.resource_get('webapp')

    hookenv.status_set('maintenance', 'installing webapp')

    # Extract tar resource
    tar = tarfile.open(whelp_tar)
    tar.extractall(WHELP_HOME)

    # Install pip3 reqs
    with chdir('/srv/whelp/whelp'):
        with open('requirements.txt', 'r') as f:
            for i in list(map(lambda b: b.strip('\n'), f.readlines())):
                pip_install(i)

    # Set permissions
    chownr(WHELP_HOME, 'www-data', 'www-data')

    # Get state files for whelp to run
    whelp.get_whelp_bucket_files()

    # Configure NGINX
    configure_site('whelp', 'whelp.vhost', 
                   port=config['port'], whelp_port=config['whelp-port'])

    # Start Supervisor
    subprocess.call('supervisord -c /etc/supervisor/supervisord.conf'.split(),
                    shell=False)

    # Render whelp supervisor.conf 
    whelp.render_whelp_supervisor_conf()

    # Open port 80
    hookenv.open_port(config['port'])

    # Set status to active
    hookenv.status_set('active', 
                       'Whelp is active on port %s' % config['port'])

    # Set whelp.available state
    set_state('whelp.available')

