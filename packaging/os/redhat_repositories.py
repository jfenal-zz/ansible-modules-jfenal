#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set et tw=120 ts=4 sw=4
# Jérôme Fenal (jfenal@redhat.com)
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: redhat_repository
short_description: Manage repositories with RHSM using the C(subscription-manager) command
description:
    - List, enable and disable repositories with the Red Hat Subscription Management entitlement platform using the C(subscription-manager) command
version_added: 2.3
author: "Jérôme Fenal (@jfenal)"
notes:
    - In order to be able to enable repositories, a system will
      need first to be subscribed to RHSM. Use the
      C(redhat_subscription) Ansible module for that matter.
requirements:
    - subscription-manager
options:
    name: 
        description:
            - I(Repoid) of repositories to enable or disable
              When specifying multiple repos, separate them with a ",".
              To specify all repositories, use "*".
        required: True
        default: null
        aliases: ['repo', 'repos']
    state:
        description:
            - whether to enable (C(enabled)) or disable (C(disabled)) a repository
        required: False
        choices: [ "enabled", "disabled" ]
        default: "enabled"
        required: False
    list: 
        description:
            - List either all repositories, or only enabled or disabled (via state)
        required: False
        default: null
'''


EXAMPLES = '''
# List repositories
- redhat_repositories: list

# Enable repositories
- redhat_repositories:
    name:
      - rhel-7-server-rpms
      - rhel-7-server-optional-rpms
    state: enabled

# Disable repositories
- redhat_repositories:
    name:
      - .*-beta-.*
      - .*-htb-.*
      - .*-eus-.*
      - .*-aus-.*
    state: disabled

'''


import os
import re
import types
import ConfigParser
import shlex
import syslog

def notice(msg):
    syslog.syslog(syslog.LOG_NOTICE, msg)



syslog.openlog('ansible-%s' % os.path.basename(__file__))

class RhsmRepository(object):
    '''
        This class to host Repository information and enable/disable per repo
    '''
    def __init__(self, module, **kwargs):
        self.module = module
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.__getattribute('_name'))

#    def enable(self):
#        '''
#            Enable or disable the named repo
#        '''
#        args = "subscription-manager repos --enable=%s" % self.__str__()
#        rc, stdout, stderr = self.module.run_command(args, check_rc=True)
#        if rc == 0:
#            return True
#        else:
#            return False
#
#
#    def disable(self):
#        '''
#            Disable repository
#        '''
#        args = "subscription-manager repos --disable=%s" % self.__str__()
#        rc, stdout, stderr = self.module.run_command(args, check_rc=True)
#        if rc == 0:
#            return True
#        else:
#            return False

    @property
    def is_enabled(self):
        return self.__getattribute__("Enabled")

    @property
    def is_disabled(self):
        return not self.__getattribute__("Enabled")

class RhsmRepositories(object):
    '''
        This class to manipulate repositories
    '''

    def __init__(self, module):
        self.module = module
	#self.repos = []
        self.repos = self._load_repo_list()

    def __iter__(self):
        return self.repos.__iter__()
    
    def _load_repo_list(self):
        """
            Loads list of all available repos, whether enabled or not
        """
    
        args = "subscription-manager repos --list"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True, environ_update=dict(LANG='C'))

        repos = []
        for line in stdout.split('\n'):

            # Remove leading+trailing whitespace
            line = line.strip()

            # An empty line implies the end of a output group
            if len(line) == 0:
		key = value = ''
		notice("New repo");
                continue

            # If a colon ':' is found, parse
            elif ':' in line:
                (key, value) = line.split(':',1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
		notice("**** key: <%s> / value: <%s> " % (key,value))
                if key in ['RepoID']:
                    # Remember the name for later processing
	    	    repo=RhsmRepository(self.module, _name=value)
                    repos.append(repo)
                    repos[-1].__setattr__(key, value)
                elif repos:
                    # Associate value with most recently recorded repo
                    repos[-1].__setattr__(key, value)
             
        return repos

    def filter(self, state=None):
        ''' 
            Return a list of Repositories where state matches (null: all, enabled, disabled)
        '''
        if state == 'all' or state is None:
            for repo in self.repos:
                yield repo 
        elif state == 'enabled':
            for repo in self.repos:
                if repo.is_enabled():
                    yield repo
        elif state == 'disabled':
            for repo in self.repos:
                if repo.is_disabled():
                    yield repo

    def enablerepo(self, repos=[]):
        args = "subscription-manager repos --enable=" % ",".join( [r for r in self.repos if r.is_disabled and r in repos])
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

    def disablerepo(self, repos=[]):
        args = "subscription-manager repos --disable=" % ",".join( [r for r in self.repos if r.is_enabled and r in repos])
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

    def disable_all(self):
        args = "subscription-manager repos --disable=*"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

def list_stuff(rhsmrepos, stuff):
    l=[]
    for repo in rhsmrepos.filter(stuff):
        l.append(dict(name=repo._name, enabled=repo.is_enabled))
    return l

def main():
    #
    # Initialise Ansible module
    #
    module = AnsibleModule(
                argument_spec = dict(
                    name    = dict(default=None, required=False),
                    state   = dict(default=None, choices=['enabled','disabled']),
                    list    = dict(default=None, required=False),
                ),
                required_one_of = [['name', 'list']],
                mutually_exclusive = [['name', 'list']],
                supports_check_mode = False,
            )

    #
    # Initialize RhsmRepositories
    #
    rhsmrepos = RhsmRepositories(module)

    list = module.params['list']
    name = module.params['name']
    state = module.params['state']
    #

    if list:
        result=list_stuff(rhsmrepos, state)         # FIXME : maybe review state usage here
        module.exit_json(changed=False,repos=result)

    elif name is not None:
        if name == '*':
            rhsmrepos.disable_all()
            module.exit_json(changed=True, state=state, repos=name );
        else:
            names=name.split(name)
            if state == 'enabled':
                rhsmrepos.enablerepo(names)
            elif state == 'disabled':
                rhsmrepos.disablerepo(names)

            module.exit_json(changed=True, state=state, repos=[[ names ]] );

# import module snippets
from ansible.module_utils.basic import AnsibleModule
import syslog
import pprint

if __name__ == '__main__':
    main()

