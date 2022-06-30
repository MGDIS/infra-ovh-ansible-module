from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import ovh
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def ovh_api_connect(module):
    if not HAS_OVH:
        module.fail_json(msg='Python module python-ovh is required')

    credential_keys = ['endpoint', 'application_key',
                   'application_secret', 'consumer_key']
    credential_parameters = [
        cred in module.params for cred in credential_keys]
    try:
        if all(credential_parameters):
            client = ovh.Client(
                **{credential: module.params[credential] for credential in credential_keys})
        else:
            client = ovh.Client()
    except APIError as api_error:
        module.fail_json(msg="Failed to call OVH API: {0}".format(api_error))

    return client


def ovh_argument_spec():
    return dict(
        endpoint=dict(required=False, default=None),
        application_key=dict(required=False, default=None),
        application_secret=dict(required=False, default=None),
        consumer_key=dict(required=False, default=None),
    )
