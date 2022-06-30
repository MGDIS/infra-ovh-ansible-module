#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

DOCUMENTATION = '''
---
module: domain

version_added: "0.1.0"

description:
    - Manage DNS zone records

requirements:
    - ovh >= 0.5.0

options:
    domain:
        description: 
            - The targeted domain
        required: true
        type: str
    target:
        description:
            - The value of the record
            - It can be an IP, a FQDN, a text...
        required: true
        type: str
    name:
        description:
            - The name to add or delete in the zone
        required: true
        type: str
    record_type:
        description:
            - The DNS record type
        choices: ['A', 'AAAA', 'CAA', 'CNAME', 'DKIM', 'DMARC', 'DNAME', 'LOC', 'MX', 'NAPTR', 'NS', 'PTR', 'SPF', 'SRV', 'SSHFP', 'TLSA', 'TXT']
        default: A
        type: str
    state:
        description:
            - Wether to add or delete the record
        required: false
        choices: ['present', 'absent']
        type: str
    ttl:
        description:
            - TTL associated with the DNS record
        required: false
        type: int

'''

EXAMPLES = '''
- name: Add entry
  mgdis.ovh.domain:
    domain: example.com
    target: "192.2.0.1"
    name: "www"
    state: "present"
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
        domain=dict(
            type='str',
            required=True
            ),
        target=dict(
            type='str',
            required=True
            ),
        name=dict(
            type='str',
            required=True
            ),
        record_type=dict(
            type='str',
            choices=['A', 'AAAA', 'CAA', 'CNAME', 'DKIM', 'DMARC', 'DNAME', 'LOC', 'MX', 'NAPTR', 'NS', 'PTR', 'SPF', 'SRV', 'SSHFP', 'TLSA', 'TXT'], 
            default='A'
            ),
        state=dict(
            type='str',
            choices=['present', 'absent'],
            default='present'
            ),
        ttl=dict(
            type='int',
            required=False
        )
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    client = ovh_api_connect(module)

    target = module.params['target']
    domain = module.params['domain']
    name = module.params['name']
    record_type = module.params['record_type']
    state = module.params['state']
    ttl = module.params['ttl']

    if module.check_mode:
        module.exit_json(msg="{} set to {}.{} ! - (dry run mode)".format(target, name, domain))

    try:
        available_domains = client.get('/domain/zone')
        if domain not in available_domains:
            module.fail_json(msg="Domain {} unknown".format(domain))
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    try:
        existing_records = client.get(
            '/domain/zone/%s/record' % domain,
            fieldType=record_type,
            subDomain=name
        )
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    if state == 'present':
        if len(existing_records) >= 1:
            for index in existing_records:
                try:
                    record = client.get(
                        '/domain/zone/%s/record/%s' % (domain, index)
                    )
                    if record['subDomain'] == name and record['target'] == target:
                        module.exit_json(
                            msg="{} is already registered on domain {}".format(name, domain),
                            changed=False)
                    else:
                        result = client.post(
                            '/domain/zone/%s/record' % domain,
                            fieldType=record_type,
                            subDomain=name,
                            target=target,
                            ttl=ttl
                            )
                        client.post(
                            '/domain/zone/%s/refresh' % domain
                        )
                        module.exit_json(changed=True, **result)
                except APIError as api_error:
                    module.fail_json(
                        msg="Failed to call OVH API: {0}".format(api_error))

    else:
        if not existing_records:
            module.exit_json(
                msg="Target {} doesn't exist on domain {}".format(
                    name, domain),
                changed=False)

        record_deleted = []
        try:
            for index in existing_records:
                record = client.get(
                    '/domain/zone/%s/record/%s' % (domain, index)
                )
                client.delete(
                    '/domain/zone/%s/record/%s' % (domain, index)
                )
                record_deleted.append("%s IN %s %s" % (
                    record.get('subDomain'), record.get('fieldType'), record.get('target')))
            client.post(
                '/domain/zone/%s/refresh' % domain
            )
            module.exit_json(
                msg=",".join(record_deleted) + " successfuly deleted from domain {}".format(domain),
                changed=True)
        except APIError as api_error:
            module.fail_json(
                msg="Failed to call OVH API: {0}".format(api_error))


def main():
    run_module()


if __name__ == '__main__':
    main()
