#!/usr/bin/python
# vim:  et tw=120 ts=4 sw=4
# Jerome Fenal (jfenal@redhat.com)
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
author: "Jerome Fenal (@jfenal)"
notes:
    - In order to be able to enable repositories, a system will
      need first to be subscribed to RHSM. Use the
      C(redhat_subscription) Ansible module for that matter.
requirements:
    - subscription-manager
options:
    id: 
        description:
            - I(RepoIDs) of repositories to enable or disable
              When specifying multiple repos, separate them with a ",".
              To specify all repositories, use "*".
        required: True
        default: null
    state:
        description:
            - whether to enable (C(enabled)) or disable (C(disabled)) a repository
        required: False
        choices: [ "enabled", "disabled" ]
        default: "enabled"
        required: False
    list: 
        description:
            - List either all repositories, or only enabled or disabled
        required: False
        default: all
        choices: [ "all", "enabled", "disabled" ]

'''


EXAMPLES = '''
# List all repositories
- redhat_repositories: list=all

# List enabled repositories
- redhat_repositories: list=enabled

# List disabled repositories
- redhat_repositories: list=disabled

# Enable repositories
- redhat_repositories:
    id:
      - rhel-7-server-rpms
      - rhel-7-server-optional-rpms
    state: enabled

# Disable repositories
- redhat_repositories:
    id:
      - .*-beta-.*
      - .*-htb-.*
      - .*-eus-.*
      - .*-aus-.*
    state: disabled

# Disable all repositories
- redhat_repositories: id=* state=disabled

'''


import os
import re
import types
import ConfigParser
import shlex
import syslog
import pprint
# import module snippets
from ansible.module_utils.basic import AnsibleModule

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
    def id(self):
        return self.RepoID

    @property
    def name(self):
        return self.RepoName

    @property
    def url(self):
        return self.RepoURL


    @property
    def is_enabled(self):
        return self.Enabled

    @property
    def is_disabled(self):
        return not self.Enabled

class RhsmRepositories(object):
    '''
        This class to manipulate repositories
    '''

    def __init__(self, module):
       self.module = module
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

            # An empty line implies the end of a output group, strip headers too
            if len(line) == 0 or re.match(r'^\s+.*', line) or re.match(r'^\+s.*', line):
                continue

                key = ''
                value = ''
                continue

            # If a colon ':' is found, parse
            elif ':' in line:
                (key, value) = line.split(':',1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
                if key in ['RepoID']:
                    # Remember the name for later processing
                    repos.append( RhsmRepository(self.module, _name=value) )
                    repos[-1].__setattr__(key, value)
                elif key in ['Enabled']:
                    # Use a real boolean
                    repos[-1].__setattr__(key, value == '1')
                elif repos:
                    # Associate value with most recently recorded repo
                    repos[-1].__setattr__(key, value)
             
        return repos

    def filter(self, state):
        ''' 
            Return a list of Repositories where state matches (null: all, enabled, disabled)
        '''
        if state is None or state == 'all':
            for repo in self.repos:
                yield repo 

        elif state == 'enabled':
            for repo in self.repos:
                if repo.Enabled:
                    yield repo

        elif state == 'disabled':
            for repo in self.repos:
                if not repo.Enabled:
                    yield repo

    def enablerepo(self, id):
        if len(id) > 0:
            args="subscription-manager repos "
            for n in id:
                args+=" --enable="+n
            notice("redhat_repository: enable repos args: " + args)
            rc, stdout, stderr = self.module.run_command(args, check_rc=True)

    def disablerepo(self, id):
        if len(id) > 0:
            args="subscription-manager repos "
            for n in id:
                args += " --disable=" + n 
            rc, stdout, stderr = self.module.run_command(args, check_rc=True)

    def disable_all(self):
        notice("redhat_repository: disable all repos")
        args = "subscription-manager repos --disable='*'"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

def list_stuff(rhsmrepos, stuff):
    l={}
    for repo in rhsmrepos.filter(stuff):
        id=repo.id
        id=id.replace("-", "_") 
        l[id] = dict(id=repo.id, name=repo.name, enabled=repo.is_enabled, url=repo.url)
    return l

def main():
    #
    # Initialise Ansible module
    #
    module = AnsibleModule(
                argument_spec = dict(
                    id      = dict(default=None, type="list"),
                    state   = dict(default=None, choices=['enabled','disabled']),
                    # can't set a default='all' on list, otherwise id will never be used to enable/disable repos
                    list    = dict(default=None, choices=['all','enabled','disabled']),
                ),
                required_one_of = [['id', 'list']],
                mutually_exclusive = [['id', 'list']],
                supports_check_mode = False,
            )

    #
    # Initialize RhsmRepositories
    #
    rhsmrepos = RhsmRepositories(module)

#for repo in rhsmrepos.repos: notice(pprint.pformat(repo))

    p_list = module.params['list']
    p_id = module.params['id']
    p_state = module.params['state']
    #

    msg = "redhat_repository: in main | list=" + str(p_list) + " | id=" + str(p_id) + " | state=" + str(p_state)
    notice(msg)
    if p_list is not None:
        notice("redhat_repository: in main, list is not None")
        if p_list in [ 'all', 'enabled', 'disabled' ]:
            result=list_stuff(rhsmrepos, p_list)
            module.exit_json(changed=False,repos=result)
        else:
            # we shouldn't reach this with Ansible.
            module.exit_json(changed=False,error="Unknown list primitive")

    elif p_id is not None:
       notice("redhat_repository: in main, id is not None")
       if p_state == 'enabled':
           rhsmrepos.enablerepo(p_id)
       elif p_state == 'disabled':
           notice("redhat_repository: in main, state=disabled")
           if id == '*':
               # take a shortcut
               rhsmrepos.disable_all()
           else:
               rhsmrepos.disablerepo(p_id)

       module.exit_json(changed=True, state=p_state, id=p_id);

if __name__ == '__main__':
    main()

