#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: flavor_info

version_added: "0.1.0"

description:
    - Get info on a flavor which are used on the OVH resources.

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
            - The flavor name which can be found on the OVH docs (t1-45, b2-7 etc)
        required: true
        type: str
    region:
        description:
            - The region where the flavor is looked up
        required: true
        type: str

'''

EXAMPLES = '''
- name: Get info on an instance flavor
  mgdis.ovh.flavor_info:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    region: GRA7
    name: t1-45
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
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    name = module.params['name']
    region = module.params['region']

    try:
        flavor_list = client.get('/cloud/project/%s/flavor' % (service_name), region=region)
        for flavor in flavor_list:
            if flavor['name'] == name:
                try:
                    result = client.get('/cloud/project/%s/flavor/%s' % (service_name, flavor['id']))
                    module.exit_json(changed=False, **result)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        module.fail_json(msg="Flavor {} not found in {}".format(name, region), changed=False)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
