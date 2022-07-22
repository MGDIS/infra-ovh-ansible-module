#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: reverse_dns

version_added: "0.1.0"

description:
    - Create reverse DNS for defined IP

requirements:
    - ovh >= 0.5.0

options:
    ip:
        description:
            - The IP address on which the lookup will be done
        required: true
        type: str
    domain_name:
        description:
            - The domain name to associate with the IP address
        required: true
        type: str
    ip_block:
        description:
            - The ipBlock from which the IP address is part of if reverse is based on vRack IPs
        required: false
        default: None
        type: str

'''

EXAMPLES = '''
mgdis.ovh.reverse_dns:
  ip: 192.0.2.1
  domain_name: test.example.com
'''

RETURN = ''' # '''

from ansible_collections.mgdis.ovh.plugins.module_utils.ovh import ovh_api_connect, ovh_argument_spec
import urllib.parse
import ipaddress

try:
    from ovh.exceptions import APIError, ResourceNotFoundError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def run_module():
    module_args = ovh_argument_spec()
    module_args.update(dict(
        ip=dict(
            type='str',
            required=True
        ),
        domain_name=dict(
            type='str',
            required=True
        ),
        ip_block=dict(
            type='str',
            required=False, default=None
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )
    client = ovh_api_connect(module)

    ip = module.params['ip']
    domain_name = module.params['domain_name']
    ip_block = module.params['ip_block']

    # ip_block is only needed for vrack IPs. Default it to "ip" when not used
    if ip_block is None:
        ip_block = ip
    else:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(ip_block):
            # url encode the ip mask (/26 -> %2F)
            ip_block = urllib.parse.quote(ip_block, safe='')
        else:
            module.fail_json(msg="IP {} not in IP block {}".format(ip, ip_block))

    result = {}
    try:
        result = client.get('/ip/%s/reverse/%s' % (ip_block, ip))
    except ResourceNotFoundError:
        result['reverse'] = ''

    if result['reverse'] == domain_name:
        module.exit_json(msg="Reverse {} to {} already set !".format(ip, domain_name), changed=False)

    try:
        client.post(
            '/ip/%s/reverse' % ip_block,
            ipReverse=ip,
            reverse=domain_name
        )
        module.exit_json(
            msg="Reverse {} to {} succesfully set !".format(ip, domain_name),
            changed=True)
    except APIError as api_error:
        return module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
