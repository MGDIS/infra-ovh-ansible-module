# OVH collection for Ansible

The OVH collection includes a variety of Ansible modules to help automate the management of OVH resources through API calls.

## Ansible version compatibility

This collection has been tested against following Ansible versions: >=2.12.4.

Plugins and modules within a collection may be tested with only specific Ansible versions. A collection may contain metadata that identifies these versions. PEP440 is the schema used to describe the versions of Ansible.

## Python version compatibility

This collection requires Python 3.6 or greater.


## Installing this collection

You can install the mgdis.ovh collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install mgdis.ovh

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: mgdis.ovh

```

A specific version of the collection can be installed by using the `version` keyword in the `requirements.yml` file:

```yaml
---
collections:
  - name: mgdis.ovh
    version: 0.1.0
```

You can either call modules by their Fully Qualified Collection Namespace (FQCN), such as `mgdis.ovh.db_cluster_info`, or you can call modules by their short name if you list the `mgdis.ovh` collection in the playbook's `collections` keyword:

```yaml
---
- name: Get cluster info
  mgdis.ovh.db_cluster_info:
    endpoint: "ovh-eu"
    application_key: "<application key>"
    application_secret: "<application secret>"
    consumer_key: "<consumer key>"
    service_name: "abcdefghijklmnopqrstuvwxyz012345"
    db_type: "mongodb"
    cluster_id: "myClusterName"

```
## Included content

### Modules
- mgdis.ovh.block_storage
- mgdis.ovh.block_storage_info
- mgdis.ovh.db_cluster
- mgdis.ovh.db_cluster_info
- mgdis.ovh.db_cluster_ip_restriction
- mgdis.ovh.db_cluster_user
- mgdis.ovh.flavor_info
- mgdis.ovh.image_info
- mgdis.ovh.instance_info
- mgdis.ovh.instance
- mgdis.ovh.monthly_billing
- mgdis.ovh.ip_reverse
- mgdis.ovh.domain