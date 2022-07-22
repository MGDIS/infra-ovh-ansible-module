#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: dbs_cluster_ip_restriction

version_added: "0.1.0"

description:
    - This module set the IP restrictions of a managed database cluster.

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
    ip_blocks:
        description:
            - The ip blocks to add
        required: true
        type: list

'''

EXAMPLES = '''
mgdis.ovh.db_cluster_restriction:
  service_name: abcdefghijklmnopqrstuvwxyz012345"
  name: myClusterName
  type: mongodb
  ip_blocks :
    - ip: 172.0.1.0/24
      description: mySubnet
'''

RETURN = ''' # '''

from ansible_collections.mgdis.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


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
        ip_blocks=dict(
            type='list',
            required=True,
            elements='dict',
            options=dict(
                ip=dict(
                    type='str',
                    required=True
                ),
                description=dict(
                    type='str',
                    required=False
                )
            )
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    cluster_name = module.params['name']
    service_name = module.params['service_name']
    db_type = module.params['type']
    ip_blocks = module.params['ip_blocks']

    ip_added = False
    cluster_id = ""

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

    try:
        restrictions = client.get('/cloud/project/%s/database/%s/%s/ipRestriction' % (service_name, db_type, cluster_id))
        for ip_block in ip_blocks:
            if ip_block["ip"] not in restrictions:
                client.post('/cloud/project/%s/database/%s/%s/ipRestriction' % (service_name, db_type, cluster_id), **ip_block)
                ip_added = True
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if ip_added:
        module.exit_json(changed=True)
    else:
        module.exit_json(changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
