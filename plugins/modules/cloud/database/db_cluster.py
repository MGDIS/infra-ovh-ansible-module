#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: public_cloud_dbaas_cluster

version_added: "0.1.0"

description:
    - This module manage the creation and update of a OVH public cloud dbaas cluster.

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
    version:
        description:
            - The database engine version
        required: true
        type: str
    flavor:
        description:
            - The instance type to provision for the cluster
        required: true
        type: str
    region:
        description:
            - Region hosting the cluster
        required: true
        type: str
    plan:
        description:
            - The OVH plan to use
        required: true
        type: str
    network_id:
        description:
            - The id of the private network to attach
        required: false
        type: str
    subnet_id:
        description:
            - The ID of the specific subnet to use from the private network
        required: false
        type: str

'''

EXAMPLES = '''
mgdis.ovh.db_cluster:
  service_name: abcdefghijklmnopqrstuvwxyz012345"
  name: myClusterName
  type: mongodb
  version: 5.0
  flavor: db1-2
  region: GRA
  plan: essential
  network_id: myNetwork
  subnet_id: mySubnet
'''

RETURN = ''' # '''

from ansible_collections.mgdis.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec
from deepdiff import DeepDiff

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
        version=dict(type='str', required=True),
        flavor=dict(type='str', required=True),
        region=dict(type='str', required=True),
        plan=dict(type='str', required=True),
        network_id=dict(type='str', required=False),
        subnet_id=dict(type='str', required=False),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    available = False
    exists = False
    cluster = None
    network = "public"

    name = module.params['name']
    service_name = module.params['service_name']
    db_type = module.params['type']
    version = module.params['version']
    flavor = module.params['flavor']
    region = module.params['region']
    plan = module.params['plan']
    network_id = module.params['network_id']
    subnet_id = module.params['subnet_id']
    nb_nodes = 1

    if network_id:
        network = "private"

    try:
        availability = client.get(
            '/cloud/project/%s/database/availability' % (service_name)
        )
        to_check = {
            "engine": db_type,
            "version": version,
            "plan": plan,
            "region": region,
            "flavor": flavor,
            "network": network
            }

        for offer in availability:
            diff = DeepDiff(
                offer,
                to_check,
                ignore_string_case=True,
                exclude_paths=[
                "root['default']",
                "root['startDate']",
                "root['endOfLife']",
                "root['upstreamEndOfLife']",
                "root['backup']",
                "root['minNodeNumber']",
                "root['maxNodeNumber']",
                "root['minDiskSize']",
                "root['maxDiskSize']",
                "root['status']"
                    ]
                )
            if not diff:
                available = True
                nb_nodes = offer["minNodeNumber"]
                break
        if not available:
            msg = "Failed to find availability for cluster with parameters : engine: %s, version: %s, plan: %s, region: %s, flavor: %s, network: %s" % (db_type, version, plan, region, flavor, network)
            module.fail_json(msg=msg)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if available:
        try:
            cluster_ids = client.get('/cloud/project/%s/database/%s' % (service_name, db_type))
            for cluster_id in cluster_ids:
                try:
                    cluster_values = client.get('/cloud/project/%s/database/%s/%s' % (service_name, db_type, cluster_id))
                    if cluster_values["description"] == name:
                        exists = True
                        cluster = cluster_id
                        break
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if exists:
        try:
            details = {
                "description": name,
                "flavor": flavor,
                "nodeNumber": nb_nodes,
                "plan": plan,
                "version": version
            }
            if network == "private":
                details["subnetId"] = subnet_id
            result = client.put('/cloud/project/%s/database/%s/%s' % (service_name, db_type, cluster), **details)
            module.exit_json(changed=False, **result)
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    else:
        try:
            details = {
                "description": name,
                "nodesPattern": {
                    "flavor": flavor,
                    "number": nb_nodes,
                    "region": region
                },
                "plan": plan,
                "version": version
            }
            if network == "private":
                details["networkId"] = network_id
                details["subnetId"] = subnet_id
            result = client.post('/cloud/project/%s/database/%s' % (service_name, db_type), **details)
            module.exit_json(changed=False, **result)
        except APIError as api_error:
            module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
