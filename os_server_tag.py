#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2019, Dominik Stucki <stucki@puzzle.ch>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_server_tag
short_description: Manage server tags
extends_documentation_fragment: openstack
version_added: "2.8"
author: Dominik Stucki (@n-ik)
description:
    - set or delete tags on the instance
options:
   server:
      description:
        - Name or ID of the server
      required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [ present, absent ]
     default: present
   tags:
     description:
       - Key and value for tags
     required: true
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''
EXAMPLES = '''
---
- name: set the tags on the instance
  os_server_tag:
    server: "{{ server_name }}"
    state: present
    tags:
      - key.value
'''

RETURN = '''
server:
    description: UUID of the server.
    returned: success
    type: str
    sample: 2f66c03e-a9ab-414c-925a-03eb14871456

tags:
    description: tags.
    returned: success
    type: list
    sample: ["key1.value1","key2.value2"]
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import (
    openstack_full_argument_spec, openstack_module_kwargs,
    openstack_cloud_from_module)

try:
    from openstack import connect
except ImportError:
    pass


def main():

    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        tags=dict(default=[], type='list'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    server_param = module.params['server']
    state = module.params['state']
    tags = module.params['tags']

    conn = connect()
    sdk, cloud = openstack_cloud_from_module(module)

    try:
        changed = False
        server = cloud.get_server(server_param)
        if not server:
            module.fail_json(msg="server not found: %s " % server_param)

        server = conn.compute.get_server(server.id)
        current_tagging = server.fetch_tags(conn.compute)

        if state == 'present':
            if set(current_tagging.tags) != set(tags):
                if not module.check_mode:
                    server.set_tags(conn.compute, tags)
                changed = True
        elif state == 'absent':
            for tag in tags:
                if tag in current_tagging.tags:
                    if not module.check_mode:
                        server.remove_tag(conn.compute, tag)
                    changed = True

        # Refresh current tags again
        current_tagging = server.fetch_tags(conn.compute)
        module.exit_json(changed=changed, server=server.id, tags=current_tagging.tags)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
