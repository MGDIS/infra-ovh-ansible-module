#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: db_cluster_info

version_added: "0.1.0"

description:
    - This module retrieves all info of a managed database cluster.
    
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
'''

EXAMPLES = '''
mgdis.ovh.db_cluster_info:
  service_name: abcdefghijklmnopqrstuvwxyz012345
  name: myClusterName
  type: mongodb
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
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    cluster_name = module.params['name']
    db_type = module.params['type']
    
    info = ""

    try:
        clusters = client.get('/cloud/project/%s/database/%s' % (service_name, db_type))
        for cluster in clusters:
            try:
                result = client.get('/cloud/project/%s/database/%s/%s' % (service_name, db_type, cluster))
                if result['description'] == cluster_name:
                    info = result
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if info:
        module.exit_json(changed=False, **info)
    else:
        module.fail_json(msg="Cluster {} not found for database_type {}".format(cluster_name, db_type))

    


def main():
    run_module()


if __name__ == '__main__':
    main()
