#!/bin/bash

pushd ${0%/*}
ansible-playbook -i hosts test-01.yml
ansible-playbook -i hosts test-02.yml
ansible-playbook -i hosts test-03.yml
ansible-playbook -i hosts test-04.yml
popd
