#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: monthly_billing

version_added: "0.1.0"

description:
    - This module enables monthly billing on a public cloud instance.
    - THIS IS NOT REVERSIBLE.

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
            - The of the instance to pass to monthly billing
        required: true
        type: str

'''

EXAMPLES = '''
- name: Enable monthly billing
  mgdis.ovh.monthly_billing:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    name: myInstance
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
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    instance_name = module.params['name']

    instance_id = ''

    try:
        instances_list = client.get(
            '/cloud/project/%s/instance' % (service_name)
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    for instance in instances_list:
        if instance['name'] == name:
            instance_id = instance["id"]

    if not instance_id:
        module.fail_json(msg="Instance {} does not exist".format(instance_name))

    try:
        result = client.get('/cloud/project/%s/instance/%s' % (service_name, instance_id))
        if result['monthlyBilling'] is not None and result['monthlyBilling']['status'] == "ok":
            module.exit_json(changed=False, msg="Monthly billing already enabled")

        result = client.post('/cloud/project/%s/instance/%s/activeMonthlyBilling' % (service_name, instance_id))
        module.exit_json(changed=True, **result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        instance_list = client.get('/cloud/project/%s/instance' % (service_name))
        for instance in instance_list:
            if instance['name'] == instance_name:
                try:
                    result = client.get('/cloud/project/%s/instance/%s' % (service_name, instance['id']))
                    if result['monthlyBilling'] is not None and result['monthlyBilling']['status'] == "ok":
                        module.exit_json(changed=False, msg="Monthly billing already enabled")

                    result = client.post('/cloud/project/%s/instance/%s/activeMonthlyBilling' % (service_name, instance['id']))
                    module.exit_json(changed=True, **result)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
        module.fail_json(msg="Instance {} not found".format(instance_name))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
