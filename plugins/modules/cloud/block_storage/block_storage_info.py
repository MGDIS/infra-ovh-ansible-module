#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: block_storage_info

version_added: "0.1.0"

description:
    - This module attach or detach a volume of an instance on OVH public Cloud.

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
            - The name of the block storage
        required: true
        type: str
    region:
        description:
            - The region where the block storage will deploy
        required: true
        type: str
'''

EXAMPLES = '''
- name: Ensure Volume is affected to instance
  mgdis.ovh.block_storage_info:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    name: myBlockStorage
'''

RETURN = ''' # '''

from ansible_collections.synthesio.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec

try:
    from ovh.exceptions import APIError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        service_name=dict(
            type='str',
            required=True
        ),
        name=dict(
            type='str',
            required=True
        ),
        region=dict(
            type='str',
            required=True
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    name = module.params['name']
    region = module.params['region']

    volume_list = []
    volume_id = ""
    volume_details = {}
    try:
        volume_list = client.get('/cloud/project/%s/volume' % service_name, region=region)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    for volume in volume_list:
        if volume['name'] == name:
            volume_id = volume['id']
            try:
                volume_details = client.get('/cloud/project/%s/volume/%s' % (service_name, volume_id))
                module.exit_json(changed=True, **volume_details)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    
    # TO DO Add instance info


def main():
    run_module()


if __name__ == '__main__':
    main()
