#!/usr/bin/python
# vim: et tw=120
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
version_added: 2.1
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
        required: true
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
        required: false
        default: null
'''

import os
import re
import types
import ConfigParser
import shlex

class RhsmRepository(object):
    '''
        This class to host Repository information and enable/disable per repo
    '''
    def __init__(self, module):
        self.module = module
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.__getattribute('_name'))

    def enable(self):
        '''
            Enable or disable the named repo
        '''
        args = "subscription-manager repos --enable=%s" % self.__str__()
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)
        if rc == 0:
            return True
        else:
            return False


    def disable(self):
        '''
            Disable repository
        '''
        args = "subscription-manager repos --disable=%s" % self.__str__()
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)
        if rc == 0:
            return True
        else:
            return False

    @property
    def is_enabled(self):
        return self.__getattribute("Enabled")

    @property
    def is_disabled(self):
        return not self.__getattribute("Enabled")

class RhsmRepositories(object):
    '''
        This class to manipulate repositories
    '''

    def __init__(self, module):
        self.module = module
        self.repos = self._load_repos()

    def __iter__(self):
        return self.repos.__iter__()
    
    def _load_repos(self):
        """
            Loads list of all available repos, wether enabled or not
        """
    
        args = "subscription-manager repos --list"
        repos = []

        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

        for line in stdout.split('\n'):
            # Remove leading+trailing whitespace
            line = line.strip()
            # An empty line implies the end of a output group
            if len(line) == 0:
                continue
            # If a colon ':' is found, parse
            elif ':' in line:
                (key, value) = line.split(':',1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
                if key in ['RepoID']:
                    # Remember the name for later processing
                    repos.append(Repository(self.module, _name=value, key=value))
                elif products:
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
        

#    def disablerepo(self, repos=[]):

    def disable_all():
        args = "subscription-manager repos --disable=*"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

def list_stuff(rhsmrepos, stuff):
    l=[]
    for repo in rhsmrepos.filter(stuff):
        l.append(repo._name)
    return l

def main():
    # Initialize RhsmRepositories
    rhsmrepos = RhsmRepositories(none)

    # Initialise Ansible module
    module = AnsibleModule(
                argument_spec = dict(
                    repo = dict(default=None, required=False),
                    state = dict(default=None, choices=['enabled','disabled']),
                ),
                required_one_of = [['name','list']],
                mutually_exclusive = [['name','list']],
                supports_check_mode = False
            )

    repos.module = module

    name = module.params['name']
    do_list = module.params['list']
    state = module.params['state']

    #

    if do_list:
        results = dict(results=list_stuff(rhsmrepos, state))
    elif name is not None:
        if name == '*':
            rhsmrepos.disable_all()
        else:
            en_name=name.split(name)

            if state == 'enabled':
                rhsmrepos.enablerepo(en_name)
            elif state == 'disabled':
                rhsmrepos.disablerepo(en_name)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
