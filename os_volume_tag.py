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
module: os_volume_tag
short_description: Manage volume tags
extends_documentation_fragment: openstack
version_added: "2.8"
author: Dominik Stucki (@n-ik)
description:
    - set or delete tags on the instance
options:
   volume:
      description:
        - ID of the volume
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
  os_volume_tag:
    volume: "{{ volume_id }}"
    state: present
    tags: {"key1":"value1","key2":"value2"}
'''

RETURN = '''
volume:
    description: UUID of the volume.
    returned: success
    type: str
    sample: 2f66c03e-a9ab-414c-925a-03eb14871456

tags:
    description: tags.
    returned: success
    type: list
    sample: ["key1" : "value1", "key2" : value2]
'''

try:
    from openstack import connect
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import (
    openstack_full_argument_spec, openstack_module_kwargs,
    openstack_cloud_from_module)

argument_spec = openstack_full_argument_spec(
    volume=dict(required=True),
    state=dict(default='present', choices=['absent', 'present']),
    tags=dict(type='dict'),
)

module_kwargs = openstack_module_kwargs()
module = AnsibleModule(argument_spec,
                       supports_check_mode=True,
                        **module_kwargs)

volume = module.params['volume']
state = module.params['state']
tags = module.params['tags']

conn = connect()
sdk, cloud = openstack_cloud_from_module(module)


def current_tags():
    url = ('/os-vendor-volumes/%(volume_id)s/tags'
           % {'volume_id': volume}
          )

    response = conn.block_storage.get(url)
    current_tagging = response.json()

    # Parse current tags
    current_tags = {}
    for item in current_tagging["tags"]:
        current_tags[item["key"]] = item["value"]

    return current_tags


def rest_call(volume, action, key, value):
    url = ('/os-vendor-volumes/%(volume_id)s/tags/action'
           % {'volume_id': volume}
          )

    data = '''{
                "action": "%(action)s",
                "tags": [
                    {
                        "key": "%(key)s",
                        "value": "%(value)s"
                    }
                ]
           }''' % {'action' : action, 'key' : key, 'value' : value}

    headers = {"Content-Type": "application/json"}

    response = conn.block_storage.post(url, headers=headers, data=data)


def main():


    try:
        changed = False
        volume_info = cloud.get_volume(volume)
        if not volume_info:
            module.fail_json(msg="volume not found: %s " % volume)

        current_tagging = current_tags()

        if state == 'present':
            if current_tagging != tags:
                if not module.check_mode:
                    for key, value in tags.items():
                        rest_call(volume=volume, action="create", key=key, value=value)
                    changed = True
        elif state == 'absent':
            for key in tags.keys():
                if key in current_tagging:
                    if not module.check_mode:
                        for key, value in tags.items():
                            rest_call(volume=volume, action="delete", key=key, value=value)
                        changed = True

        # Refresh current tags again
        current_tagging = current_tags()
        module.exit_json(changed=changed, volume=volume, tags=current_tagging)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
