# Copyright 2020 The tfaip authors. All Rights Reserved.
#
# This file is part of tfaip.
#
# tfaip is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# tfaip is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# tfaip. If not, see http://www.gnu.org/licenses/.
# ==============================================================================
import json
import unittest
import os
from typing import List
import sys
import yaml
import git

this_dir = os.path.dirname(os.path.realpath(__file__))
drone_cfg_file_path = os.path.abspath(os.path.join(this_dir, '..', '.drone.yml'))
sys.path.insert(0, os.path.abspath(os.path.join(this_dir, '..')))  # Add so that python/generate.py works


def list_tests(suite=unittest.defaultTestLoader.discover(os.path.join(this_dir, '..'))):
    if hasattr(suite, '__iter__'):
        return sum([list_tests(x) for x in suite], [])
    return [suite]


all_tests = list_tests()


def new_step(name, commands, depends_on=None, environment=None):
    step = {
        'name': name,
        'image': 'planet:python3',
        'volumes': [
            {'name': 'pip_cache', 'path': '/root/.cache/pip'},
            {'name': 'venv', 'path': '/root/venv'},
        ],
        'commands': commands,
    }
    if depends_on:
        step['depends_on'] = depends_on
    if environment:
        step['environment'] = environment

    return step


def prepare_step():
    return new_step('prepare', [
        'cd $DRONE_WORKSPACE_BASE',
        'mkdir logs',
        'virtualenv -p python3 /root/venv',
        # The following line fixes a weired pip bug by reinstalling newest pip in the venv
        'wget https://bootstrap.pypa.io/get-pip.py && /root/venv/bin/python3 get-pip.py',
        '/root/venv/bin/pip install -U pip setuptools',
        '/root/venv/bin/pip install --use-feature 2020-resolver -r requirements.txt',
        '/root/venv/bin/pip install --use-feature 2020-resolver -r test_requirements.txt',
        '/root/venv/bin/python setup.py install',
    ])


def integrity_check_step():
    return new_step('Integrity check ', [
        'cd $DRONE_WORKSPACE_BASE',
        'echo $PWD',
        'PYTHONPATH=$PWD /root/venv/bin/python drone/integrity_check.py ' + " ".join(t.id() for t in all_tests)
    ],
             )


def all_test_steps(filter: List[str] = []):
    steps = []
    all_test_names_in_drone = []
    for test in all_tests:
        if filter:
            if not any(f in test.id() for f in filter):
                continue
        name = test.id()[-100:]  # Maximum name length is 100 in drone
        all_test_names_in_drone.append(name)
        step = new_step(
            name=name,
            commands=[
                'cd $DRONE_WORKSPACE_BASE',
                '. /root/venv/bin/activate',
                f'/root/venv/bin/python -m unittest {test.id()}'
            ],
            # depends_on=['prepare'] + all_test_names_in_drone[-1:],  # hack to run only one in parallel
        )
        step['when'] = {
            'status': ['failure', 'success']  # Force to run even if prev step failed
        }
        steps.append(step)

    return steps


def notify_step():
    step = new_step(name='notify', commands=[
        'cd $DRONE_WORKSPACE_BASE',
        'export PYTHONPATH=$PWD',
        'git clone --depth=1 -b devel https://gitea.planet-ai.de/pai/cicd',
        'echo "The repository $DRONE_REPO_NAME/$DRONE_BRANCH has been changed and contains errors." > message.txt',
        'echo "" >> message.txt',
        'echo "Failed stages:" $DRONE_FAILED_STAGES >> message.txt',
        'echo "Failed steps:" >> message.txt',
        'echo $DRONE_FAILED_STEPS >> message.txt',
        'echo "Please check the links for more information." >> message.txt',
        'echo "Errors and changes leading to failure:" >> message.txt',
        'echo "  $CI_BUILD_LINK" >> message.txt',
        'echo "  $DRONE_BUILD_LINK" >> message.txt',
        'echo "getting username of last committers"',
        'USERNAME=$(python3 cicd/noarch/getLastCommitter.py -repo $DRONE_REPO_NAME -auth_key $GIT_AUTH_KEY)',
        'echo "found username - $USERNAME"',
        'cat message.txt',

        'if [ "$USERNAME" ] ; then',
        'python3 cicd/noarch/getContacts.py -a $ADMIN_EMAIL -r $DRONE_REPO_NAME -u $USERNAME -o cicd/maintainer.lst -c cicd/contact.lst -f mailto > recipients.txt',
        'else',
        'python3 cicd/noarch/getContacts.py -a $ADMIN_EMAIL -r $DRONE_REPO_NAME -o cicd/maintainer.lst -c cicd/contact.lst -f mailto > recipients.txt',
        'fi',
        'echo "Sending notification to:"',
        'cat recipients.txt',
        'python3 cicd/noarch/e_mail.py -u $EMAIL_USERNAME -p $EMAIL_PASSWORD -f $FROM -t `cat recipients.txt` -s "DRONE:$DRONE_REPO/$DRONE_BRANCH changed" -m message.txt',
    ],
                           # depends_on=all_test_names_in_drone,
                           )
    step['environment'] = {
        'SUBJECT': "Changes/Errors:$DRONE_REPO",
        'ADMIN_EMAIL': {'from_secret': 'DRONE_ADMIN_EMAIL'},
        'FROM': {'from_secret': 'DRONE_EMAIL'},
        'EMAIL_USERNAME': {'from_secret': 'DRONE_EMAIL_USERNAME'},
        'EMAIL_PASSWORD': {'from_secret': 'DRONE_EMAIL_PASSWORD'},
        'GIT_AUTH_KEY': {'from_secret': 'DRONE_MACHINE_USER_GITEA_KEY'},
    }
    step['when'] = {
        'status': ['failure']
    }
    return step


def pipeline(
        name: str,
        trigger: dict,
        test_steps: list,
):
    steps = [
        prepare_step(),
        integrity_check_step(),
        ] + test_steps + [
        notify_step(),
    ]
    drone_cfg = {
        'kind': 'pipeline',
        'type': 'docker',
        'name': name,
        'steps': steps,
        'volumes': [
            {'name': 'docker', 'host': {'path': '/var/run/docker.sock'}},
            {'name': 'pip_cache', 'temp': {}},
            {'name': 'venv', 'temp': {}},
        ],
        'trigger': trigger,
    }

    return drone_cfg


def generate_drone_cfg():
    with open(os.path.join(this_dir, 'branch_config.json')) as f:
        cfg = json.load(f)

    repo = git.Repo(os.path.join(this_dir, '..'))
    branch_name = repo.active_branch.name
    additional_tests_for_branch = cfg.get(branch_name, [])
    ignore_tests_for_branches = [t[1:] for t in additional_tests_for_branch if t[0] == '!']
    base_tests = ['test.base', 'test.scenario.tutorial', 'test.scripts']
    filtered_tests = [t for t in base_tests if t not in ignore_tests_for_branches]
    filtered_tests.extend(additional_tests_for_branch)
    all_pipelines = [
        pipeline(
            name='full_pipeline',
            trigger={
                'branch': ['master', 'devel', 'fix/*', 'issue/*', 'run-test/*'],
                'event': ['push'],
            },
            test_steps=all_test_steps(),
        ),
        pipeline(
            name='pull_request',
            trigger={
                'event': ['pull_request'],
            },
            test_steps=all_test_steps(),
        ),
        pipeline(
            name='feature_full',
            trigger={
                'branch': ['feature/*'],
                'event': ['cron'],
                'cron': ['nightly'],
            },
            test_steps=all_test_steps(),
        ),
        pipeline(
            name='feature_reduced',
            trigger={
                'branch': ['feature/*'],
                'event': ['push']
            },
            test_steps=all_test_steps(filter=['test.base', 'test.scenario.tutorial', 'test.scripts'] + additional_tests_for_branch)
        )
    ]
    return all_pipelines


if __name__ == '__main__':
    with open(drone_cfg_file_path, 'w') as f:
        yaml.safe_dump_all(generate_drone_cfg(), f, default_flow_style=False, sort_keys=False)
