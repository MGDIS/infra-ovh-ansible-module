#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: instance

version_added: "0.1.0"

description:
    - This module creates or deletes an OVH public cloud instance

requirements:
    - ovh >= 0.5.0

options:
    name:
        description:
            - The name of the instance to create
        required: true
        type: str
    ssh_key_name:
        description:
            - The name of the ssh key used for the ssh connection
        required: false
        type: str
    flavor_name:
        description:
            - The flavor name which can be found on the OVH docs (t1-45, b2-7 etc)
        required: true
        type: str
    image_name:
        description:
            - The image or snapshot name to look for
        required: true
        type: str
    region:
        description:
            - The region where to deploy the instance
        required: true
        type: str
    networks:
        description:
            - Networks to attach to the instance
        required: false
        type: list
    service_name:
        description:
            - The OVH service name.
            - It is equal to the ID of the project in the OVH portal
        required: true
        type: str
    monthly_billing:
        description:
            - Define is the instance should be created with monthly billing
            - If true, it cannot be changed afterwards
        default: false
        type: bool
    state:
        description:
            - The state of the instance
        default: present
        type: str
        choices: ['present', 'absent']

'''

EXAMPLES = '''
- name: Instance installation
  mgdis.ovh.instance:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    name: myInstance
    ssh_key_name: test
    networks: "{{ networks }}"
    flavor_name: b2-7
    region: GRA9
    image_name: "Centos 7"
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
        name=dict(
            type='str',
            required=True
        ),
        flavor_name=dict(
            type='str',
            required=True
        ),
        image_name=dict(
            type='str',
            required=True
        ),
        service_name=dict(
            type='str',
            required=True
        ),
        ssh_key_name=dict(
            type='str',
            required=False,
            default=None
        ),
        region=dict(
            type='str',
            required=True
        ),
        networks=dict(
            type='list',
            default=[],
            elements='dict',
            options=dict(
                ip=dict(
                    type='str',
                    required=False
                ),
                network_id=dict(
                    type='str',
                    required=False
                )
            )
        ),
        monthly_billing=dict(
            type='bool',
            default=False
        ),
        state=dict(
            type=str,
            choices=['present', 'absent'],
            default='present'
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    name = module.params['name']
    service_name = module.params['service_name']
    flavor_name = module.params['flavor_name']
    image_name = module.params['image_name']
    ssh_key_name = module.params['ssh_key_name']
    region = module.params['region']
    networks = module.params['networks']
    monthly_billing = module.params['monthly_billing']
    state = module.params['state']

    flavor_id = ''
    image_id = ''
    ssh_key_id = ''

    try:
        instances_list = client.get('/cloud/project/%s/instance' % (service_name),
                                    region=region)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    for instance in instances_list:
        if instance['name'] == name:
            if state == "present":
                module.exit_json(
                    changed=False,
                    msg="Instance {} [{}] in region {} is already installed".format(name, instance_id, region)
                )
            else:
                client.delete('/cloud/project/%s/instance/%s' % (service_name, instance['id']))
                module.exit_json(msg="Instance {} deleted".format(name), changed=True)

    try:
        flavor_list = client.get('/cloud/project/%s/flavor' % (service_name), region=region)
        for flavor in flavor_list:
            if flavor['name'] == flavor_name:
                flavor_id = flavor['id']
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        ssh_key_list = client.get('/cloud/project/%s/sshkey' % (service_name), region=region)
        for ssh_key in ssh_key_list:
            if ssh_key['name'] == ssh_key_name:
                ssh_key_id = ssh_key['id']
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        image_list = client.get('/cloud/project/%s/image' % (service_name), region=region)
        for image in image_list:
            if image['name'] == image_name:
                image_id = image['id']
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        result = client.post('/cloud/project/%s/instance' % service_name,
                             flavorId=flavor_id,
                             imageId=image_id,
                             monthlyBilling=monthly_billing,
                             name=name,
                             region=region,
                             networks=networks,
                             sshKeyId=ssh_key_id
                             )

        module.exit_json(changed=True, **result)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
