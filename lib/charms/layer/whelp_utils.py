#!/usr/bin/python3
import os
import subprocess
import tarfile
import swiftclient

from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core.templating import render


config = hookenv.config()


WHELP_HOME = '/srv/whelp'
STATE_HOME = '/srv'


class Whelp:
    def __init__(self):
        self.snowflake_address = config['snowflake-address']
        self.swift_bucket_user = config['swift-bucket-user']
        self.swift_bucket_pass = config['swift-bucket-pass']
        self.swift_bucket_tenant = config['swift-bucket-tenant']
        self.swift_bucket_url = config['swift-bucket-url']
        self.swift_object = config['swift-object']
        self.swift_container = config['swift-container']
        self.state_tar = os.path.join(STATE_HOME, 'state.tar.gz')
        self.whelp_supervisor_conf = '/etc/supervisor/conf.d/whelp.conf'


    def get_whelp_bucket_files(self):
        '''
        Retrieves the initial state files from bucket storage
        '''

        swift = swiftclient.client.Connection(authurl=self.swift_bucket_url,
                                              user=self.swift_bucket_user,
                                              key=self.swift_bucket_pass,
                                              tenant_name=self.swift_bucket_tenant,
                                              cacert=None,
                                              insecure=False,
                                              auth_version="2.0")
    
        resp_headers, obj_contents = swift.get_object(self.swift_container,
                                                      self.swift_object)
    
        with open(self.state_tar, 'wb') as state_tar:
            state_tar.write(obj_contents)
    
        tar = tarfile.open(self.state_tar)
        tar.extractall(STATE_HOME)
    
    
    def render_whelp_supervisor_conf(self):
    
        """ Render /etc/supervisor/conf.d/whelp.conf
            and restart supervisor process.
        """
        if os.path.exists(self.whelp_supervisor_conf):
            subprocess.call('supervisorctl stop whelp'.split(), shell=False)
            os.remove(self.whelp_supervisor_conf)
    
        render(source='whelp.conf',
               target=self.whelp_supervisor_conf,
               owner='root',
               perms=0o644,
               context={})
    
        # Reread supervisor .conf and start/restart process
        subprocess.call('supervisorctl reread'.split(), shell=False)
        subprocess.call('supervisorctl update'.split(), shell=False)
        subprocess.call('supervisorctl start whelp'.split(), shell=False)
    
        # Restart NGINX
        host.service_restart('nginx')
