#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = '''
---
module: block_storage

version_added: "0.1.0"

description:
    - This module creates, updates or deletes a block storage volume on OVH public cloud.
    - This module can attach or detach a block storage to an instance on OVH public cloud.
    - When state is attach, the block storage is created if it does not exist.
    - When state is absent, the block storage is detached if it is paired with an instance.

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
    description:
        description:
            - The description to associate the block storage with
        required: false
        type: str
    region:
        description:
            - The region where the block storage will deploy
        required: true
        type: str
    size:
        description:
            - The size of the block storage in GB
        required: false
        type: integer
    volume_type:
        description:
            - The type of the block storage
        default: classic
        type: str
        required: false
        choices: ['classic', 'high-speed', 'high-speed-gen2']
    image_name:
        description:
            - The name of the image/os to deploy on the volume to make it bootable
        required: false
        type: str
    snapshot_name:
        description:
            - The name of the snapshot from which the block storage will be created
        required: false
        type: str
    instance_name:
        description:
            - The  instance name to which the block storage will be attached to
        required: false
        type: str
    upsize:
        description:
            - Enable to increase block storage size
        required: false
        default: false
        type: bool
    state:
        description:
            - The desired state of the block storage
        choices: ['present','absent','attach','detach']
        default: present
        required: false
        type: str
'''

EXAMPLES = '''
- name: Ensure Volume is affected to instance
  mgdis.ovh.block_storage:
    service_name: abcdefghijklmnopqrstuvwxyz012345
    region: GRA
    size: 20
    name: myBlockStorage
    description: Example
    volume_type: classic
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
        description=dict(
            type='str',
            required=False
        ),
        region=dict(
            type='str',
            required=True
        ),
        size=dict(
            type='int',
            required=False
        ),
        volume_type=dict(
            type='str',
            choices=['classic', 'high-speed', 'high-speed-gen2'],
            default='classic',
            required=False
        ),
        image_name=dict(
            type='str',
            required=False
        ),
        snapshot_name=dict(
            type='str',
            required=False
        ),
        instance_name=dict(
            type='str',
            required=False
        ),
        upsize=dict(
            type='bool',
            default=False,
            required=False
        ),
        state=dict(
            type='str',
            choices=['present','absent','attach','detach'],
            default='present',
            required=False
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    service_name = module.params['service_name']
    name = module.params['name']
    description = module.params['description']
    region = module.params['region']
    size = module.params['size']
    volume_type = module.params['volume_type']
    image_name = module.params['image_name']
    snapshot_name = module.params['snapshot_name']
    instance_name = module.params['instance_name']
    upsize = module.params['upsize']
    state = module.params['state']

    
    volume_list = []
    volume_id = ""
    volume_details = {}

    instance_list = []
    instance_id = ""

    #if module.check_mode:
    #    module.exit_json(msg="Ensure volume id {} is {} on instance id {} - (dry run mode)".format(
    #                        volume_id,
    #                        state,
    #                        instance_id
    #                        ),
    #                    changed=True
    #                    )

    try:
        volume_list = client.get('/cloud/project/%s/volume' % service_name, region=region)
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    for volume in volume_list:
        if volume['name'] == name:
            volume_id = volume['id']
            try:
                volume_details = client.get('/cloud/project/%s/volume/%s' % (service_name, volume_id))
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if volume_id:
        if state == "present" or state == "attach":
            if upsize:
                if volume_details["size"] <= size:
                    module.fail_json(msg="Cannot downsize a block storage")
                else:
                    try:
                        client.post('/cloud/project/%s/volume/%s/upsize' % (service_name, volume_id),
                            size=size
                        )
                    except APIError as api_error:
                        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
            if state == "attach":
                try:
                    instance_list = client.get('/cloud/project/%s/instance' % (service_name))
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

                for instance in instance_list:
                    if instance['name'] == instance_name:
                        instance_id = instance['id']

                if instance_id in volume_details["attachedTo"]:
                    module.exit_json(
                    msg="Block storage {} already exists and attached to {}".format(name, instance_name),
                    changed=False
                    )
                else:
                    try:
                        result = client.post('/cloud/project/%s/volume/%s/attach' % (service_name, volume_id),
                            instanceId=instance_id
                        )
                        module.exit_json(changed=True, **result)
                    except APIError as api_error:
                        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
            else:
                if size:
                    module.exit_json(msg="Size of block storage {} updated".format(name), changed=True)
                else:
                    module.exit_json(msg="Block storage {} already exists".format(name), changed=False)
        if state == "absent" or state == "detach":
            if volume_details["attachedTo"]:
                for instance in volume_details["attachedTo"]:
                    try:
                        detach = client.post('/cloud/project/%s/volume/%s/detach' % (service_name, volume_id),
                            instanceId=instance
                        )
                        while detach["status"] == "detaching":
                            try:
                                detach = client.get('/cloud/project/%s/volume/%s' % (service_name, volume_id))
                            except APIError as api_error:
                                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
                    except APIError as api_error:
                        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
            if state == 'detach':
                if volume_details["attachedTo"]:
                    module.exit_json(msg="Block storage {} detached".format(name), changed=True)
                else:
                    module.exit_json(msg="Block storage {} is not attached to an instance".format(name), changed=False)
            else:
                try:
                    _ = client.delete('/cloud/project/%s/volume/%s' % (service_name, volume_id))
                    module.exit_json(msg="Block storage {} has been deleted".format(name), changed=True)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
    else:
        if state == "absent" or state == "detach":
            module.exit_json(msg="Block storage {} does not exist".format(name), changed=False)
        if state == "present" or state == "attach":
            image_id = ""
            snapshot_id = ""

            if image_name:
                try:
                    images = client.get('/cloud/project/%s/image' % service_name, region=region)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
                for image in images:
                    if image["name"] == image_name:
                        image_id = image["id"]

            if snapshot_name:
                try:
                    snapshots = client.get('/cloud/project/%s/snapshot' % (service_name))
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
                for snapshot in snapshots:
                    if snapshot["name"] == snapshot_name:
                        snapshot_id = snapshot["id"]

            payload = {
                "name": name,
                "description": description,
                "size": size,
                "region": region,
                "type": volume_type,
                "image_id": image_id,
                "snapshot_id": snapshot_id
            }
            result = ""
            try:
                result = client.post('/cloud/project/%s/volume' % (service_name), **payload)
            except APIError as api_error:
                module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))
            if state == 'present':
                module.exit_json(changed=True, **result)
            else:
                try:
                    instance_list = client.get('/cloud/project/%s/instance' % (service_name))
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

                for instance in instance_list:
                    if instance['name'] == instance_name:
                        instance_id = instance['id']
                try:
                    attach = client.post('/cloud/project/%s/volume/%s/attach' % (service_name, result["id"]),
                        instanceId=instance_id
                    )
                    module.exit_json(changed=True, **attach)
                except APIError as api_error:
                    module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
