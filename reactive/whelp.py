#!/usr/bin/python3
import os
import subprocess

from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_state

from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core.templating import render
from charmhelpers.core.host import chdir
from charmhelpers.core.host import chownr
from charmhelpers.contrib.python.packages import pip_install

import tarfile

from nginxlib import configure_site


config = hookenv.config()

WHELP_HOME = '/srv/whelp'
WHELP_VARS = '/srv/whelp/whelp/straight_script/vars/__init__.py'
WHELP_SUPERVISOR_CONF = '/etc/supervisor/conf.d/whelp.conf'


def _render_snowflake_env_var():
    '''
    Render init file for SNOWFLAKE_ADDRESS variable
    '''

    snowflake_env_cmd = 'echo "SNOWFLAKE_ADDRESS=%s" >> /etc/environment' % \
                        config['snowflake-address'] 

    swift_bucket_user_cmd = 'echo "SWIFT_BUCKET_USER=%s" >> /etc/environment' % \
                            config['swift-bucket-user']
    swift_bucket_pwd_cmd = 'echo "SWIFT_BUCKET_PASS=%s" >> /etc/environment' % \
                           config['swift-bucket-pass']
    os_tenant_cmd = 'echo "SWIFT_BUCKET_TENANT=%s" >> /etc/environment' % \
                      config['swift-bucket-tenant']
    swift_container_cmd = 'echo "SWIFT_CONTAINER=%s" >> /etc/environment' % \
                           config['swift-container']
    swift_obj_cmd = 'echo "SWIFT_OBJECT=%s" >> /etc/environment' % \
                    config['swift-object']
    swift_url_cmd = 'echo "SWIFT_BUCKET_URL=%s" >> /etc/environment' % \
                    config['swift-bucket-url']

    subprocess.call(snowflake_env_cmd.split(), shell=False)
    execfile('/etc/environment')


def _get_whelp_bucket_files():

    '''
    Retrieves the initial state files from bucket storage
    '''

    username = os.environ.get('SWIFT_BUCKET_USER', '')
    password = os.environ.get('SWIFT_BUCKET_PASS', '')
    tenant_name = os.environ.get('SWIFT_BUCKET_TENANT', '')
    auth_url = os.environ.get('SWIFT_BUCKET_URL', '')
    self.container = os.environ.get('SWIFT_CONTAINER', '')
    self.obj = os.environ.get('SWIFT_OBJECT', '')

    cacert = None
    insecure = False

    self.swift = swiftclient.client.Connection(authurl=auth_url,
                                               user=username,
                                               key=password,
                                               tenant_name=tenant_name,
                                               cacert=cacert,
                                               insecure=insecure,
                                               auth_version="2.0")

    resp_headers, obj_contents = self.swift.get_object(self.container,
                                                       self.OBJ)
    tarfile_path = WHELP_HOME + '/state.tar.gz'
    with open(tarfile_path, 'wb') as local:
        local.write(obj_contents)

    tar = tarfile.open(tarfile_path)
    tar.extractall(WHELP_HOME)


def _render_whelp_supervisor_conf():

    """ Render /etc/supervisor/conf.d/whelp.conf
        and restart supervisor process.
    """
    if os.path.exists(WHELP_SUPERVISOR_CONF):
        subprocess.call('supervisorctl stop whelp'.split(), shell=False)
        os.remove(WHELP_SUPERVISOR_CONF)

    render(source='whelp.conf',
           target=WHELP_SUPERVISOR_CONF,
           owner='root',
           perms=0o644,
           context={})

    # Reread supervisor .conf and start/restart process
    subprocess.call('supervisorctl reread'.split(), shell=False)
    subprocess.call('supervisorctl update'.split(), shell=False)
    subprocess.call('supervisorctl start whelp'.split(), shell=False)

    # Restart NGINX
    host.service_restart('nginx')


@when_not('whelp.installed')
def install_whelp():
    '''
    Reactive hook to install whelp
    '''
    hookenv.status_set('maintenance', 'Installing whelp')
    
    web_tar = hookenv.resource_get('webapp')

    hookenv.status_set('maintenance', 'installing webapp')

    # Extract tar resource
    tar = tarfile.open(web_tar)
    tar.extractall(WHELP_HOME)

    # Install pip3 reqs
    with chdir('/srv/whelp/whelp'):
        with open('requirements.txt', 'r') as f:
            for i in list(map(lambda b: b.strip('\n'), f.readlines())):
                pip_install(i)

    # Set permissions
    chownr(WHELP_HOME, 'www-data', 'www-data')

    # Render vars to /etc/environments
    _render_snowflake_env_var()

    # Get state files for whelp to run
    _get_whelp_bucket_files()

    # Configure NGINX
    configure_site('whelp', 'whelp.vhost', 
                   port=config['port'], whelp_port=config['whelp-port'])

    # Start Supervisor
    subprocess.call('supervisord -c /etc/supervisor/supervisord.conf'.split(),
                    shell=False)

    # Render whelp supervisor.conf 
    _render_whelp_supervisor_conf()

    # Open port 80
    hookenv.open_port(config['port'])

    # Set status to active
    hookenv.status_set('active', 
                       'Whelp is active on port %s' % config['port'])

    # Set whelp.available state
    set_state('whelp.available')

