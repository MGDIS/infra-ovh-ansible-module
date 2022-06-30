#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: image_info

version_added: "0.1.0"

description:
    - This module retrieves the info of an image or a snapshot.
    - It searches the image by the name provided for a specific region.

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
            - The image or snapshot name to look for
        required: true
        type: str
    region:
        description:
            - The region where the image should be
        required: true
        type: str

'''

EXAMPLES = '''
- name: Get image info
  mgdis.ovh.image_info:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    name: "Centos 7"
    region: GRA7
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
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    name = module.params['name']
    region = module.params['region']

    try:
        image_list = client.get('/cloud/project/%s/image' % (service_name), region=region)
        for image in image_list:
            if image['name'] == name:
                try:
                    result = client.get('/cloud/project/%s/image/%s' % (service_name, image['id']), region=region)
                    module.exit_json(changed=False, **result)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        snpashot_list = client.get('/cloud/project/%s/snapshot' % (service_name), region=region)
        for snapshot in snapshot_list:
            if snapshot['name'] == name:
                try:
                    result = client.get('/cloud/project/%s/snapshot/%s' % (service_name, snapshot['id']), region=region)
                    module.exit_json(changed=False, **result)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    module.fail_json(msg="Image {} not found in {}".format(name, region), changed=False)


def main():
    run_module()


if __name__ == '__main__':
    main()
