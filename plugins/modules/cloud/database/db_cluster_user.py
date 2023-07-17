#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: db_cluster_user

version_added: "0.1.0"

description:
    - This module manage the creation of a OVH public cloud dbaas users.

requirements:
    - ovh >= 0.5.0

options:
    service_name:
        description:
            - The OVH service name.
            - It is equal to the ID of the project in the OVH portal
        required: true
        type: str
    name:
        description:
            - The name of the cluster to look for
        required: true
        type: str
    type:
        description:
            - The database type
        required: true
        type: str
        choices: ['kafka', 'mongodb', 'mysql', 'opensearch', 'postgresql', 'redis']
    username:
        description:
            - Username of the user to create or update
        required: true
        type: str
    roles:
        description:
            - The roles to associate with the user
        required: false
        type: list
    state:
        description:
            - If the user should be created or deleted
        required: true
        type: str

'''

EXAMPLES = '''
mgdis.ovh.db_cluster_user:
  service_name: abcdefghijklmnopqrstuvwxyz012345"
  name: myClusterName
  type: mongodb
  username: test
  roles: dbAdmin
  state: present
'''

RETURN = ''' # '''

from ansible_collections.mgdis.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec
import re
import time

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def get_userid(module, client, details, service_name, db_type, cluster_id):
    user = ""
    try:
        user_ids = client.get(
            '/cloud/project/%s/database/%s/%s/user' % (service_name, db_type, cluster_id)
        )
        for user_id in user_ids:
            u = client.get(
                '/cloud/project/%s/database/%s/%s/user/%s' % (service_name, db_type, cluster_id, user_id)
            )
            if details["name"] == re.sub("@.+", "", u["username"]):  # Todo split u["username"] for better comparison
                user = user_id
                break
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    return user


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(type='str', required=True),
        name=dict(type='str', required=True),
        type=dict(
            type='str',
            required=True,
            choices=['kafka', 'mongodb', 'mysql', 'opensearch', 'postgresql', 'redis']
        ),
        username=dict(type='str', required=True),
        roles=dict(type='list', element='str', required=False),
        state=dict(
            type='str',
            required=False,
            choices=['present', 'absent', 'reset'],
            default='present'
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    cluster_name = module.params['name']
    service_name = module.params['service_name']
    db_type = module.params['type']
    username = module.params['username']
    roles = module.params['roles']
    state = module.params['state']

    user = ""
    cluster_id = ""
    status = "PENDING"

    details = {
        "name": username,
        "roles": roles
    }

    try:
        clusters = client.get('/cloud/project/%s/database/%s' % (service_name, db_type))
        for cluster in clusters:
            try:
                result = client.get('/cloud/project/%s/database/%s/%s' % (service_name, db_type, cluster))
                if result['description'] == cluster_name:
                    cluster_id = cluster
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if not cluster_id:
        module.fail_json(msg="Cluster {0} not found".format(cluster_name))

    user = get_userid(module, client, details, service_name, db_type, cluster_id)

    if state == 'present':
        if user:
            while status != 'READY':
                time.sleep(2)
                try:
                    u = client.get(
                        '/cloud/project/%s/database/%s/%s/user/%s' % (service_name, db_type, cluster_id, user)
                    )
                    if details["name"] == re.sub("@.+", "", u["username"]):
                        status = u["status"]
                        for actualRole in u["roles"]:
                            if actualRole not in roles:
                                roles.append(actualRole)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API0: {0}".format(api_error))
            try:
                details.pop("name")
                details["roles"] = roles
                client.put(
                    '/cloud/project/%s/database/%s/%s/user/%s' % (service_name, db_type, cluster_id, user),
                    **details
                )
                module.exit_json(changed=True)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    elif state == 'absent':
        if user:
            try:
                client.delete(
                    '/cloud/project/%s/database/%s/%s/user/%s' % (service_name, db_type, cluster_id, user)
                )
                module.exit_json(changed=True)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        else:
            module.exit_json(changed=False)
    else:
        if user:
            try:
                result = client.post(
                    '/cloud/project/%s/database/%s/%s/user/%s/credentials/reset' % (service_name, db_type, cluster_id, user)
                )
                module.exit_json(changed=True, **result)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        else:
            module.fail_json(msg="User not found")


def main():
    run_module()


if __name__ == '__main__':
    main()
