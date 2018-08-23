# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: clints
    plugin_type: inventory
    short_description: inventory source for CLINTs
    requirements:
        - boto3
        - botocore
    extends_documentation_fragment:
        - constructed
    description:
        - Get inventory hosts for the CLINTs created by qa-scale-lab repo
        - Uses a <name>.clints.yaml YAML configuration file.
    options:
        plugin:
            description: token that ensures this is a source file for the 'clints' plugin.
            required: True
            choices: ['clints', 'clint']
        boto_profile:
          description: The boto profile to use.
          env:
              - name: AWS_PROFILE
              - name: AWS_DEFAULT_PROFILE
        aws_access_key_id:
          description: The AWS access key to use. If you have specified a profile, you don't need to provide
              an access key/secret key/session token.
          env:
              - name: AWS_ACCESS_KEY_ID
              - name: AWS_ACCESS_KEY
              - name: EC2_ACCESS_KEY
        aws_secret_access_key:
          description: The AWS secret key that corresponds to the access key. If you have specified a profile,
              you don't need to provide an access key/secret key/session token.
          env:
              - name: AWS_SECRET_ACCESS_KEY
              - name: AWS_SECRET_KEY
              - name: EC2_SECRET_KEY
        aws_security_token:
          description: The AWS security token if using temporary access and secret keys.
          env:
              - name: AWS_SECURITY_TOKEN
              - name: AWS_SESSION_TOKEN
              - name: EC2_SECURITY_TOKEN
        regions:
          description: A list of regions in which to describe EC2 instances. By default this is all regions except us-gov-west-1
              and cn-north-1.
'''

EXAMPLES = '''

# Minimal example using environment vars or instance role credentials
# Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address
plugin: clints
regions:
  - us-east-2
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.plugins.inventory import BaseInventoryPlugin
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


try:
    import boto3
    import botocore
except ImportError:
    raise AnsibleError('The CLINT discovery system plugin requires boto3 and botocore.')


class InventoryModule(BaseInventoryPlugin):

    NAME = 'clints'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.group_prefix = 'clints_'

        # credentials
        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None

    def _get_credentials(self):
        '''
            :return A dictionary of boto client credentials
        '''
        boto_params = {}
        for credential in (('aws_access_key_id', self.aws_access_key_id),
                           ('aws_secret_access_key', self.aws_secret_access_key),
                           ('aws_session_token', self.aws_security_token)):
            if credential[1]:
                boto_params[credential[0]] = credential[1]

        return boto_params

    def _boto3_conn(self, regions):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''

        credentials = self._get_credentials()

        for region in regions:
            try:
                sess = boto3.session.Session(profile_name=self.boto_profile)
                ecs = sess.client('ecs', region, **credentials)
                ec2 = sess.client('ec2', region, **credentials)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                if self.boto_profile:
                    try:
                        sess = boto3.session.Session(profile_name=self.boto_profile)
                        ecs = sess.client('ecs', region)
                        ec2 = sess.client('ec2', region)
                    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                        raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
                else:
                    raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
            yield ec2, ecs, region

    def _set_credentials(self):
        '''
            :param config_data: contents of the inventory config file
        '''

        self.boto_profile = self.get_option('boto_profile')
        self.aws_access_key_id = self.get_option('aws_access_key_id')
        self.aws_secret_access_key = self.get_option('aws_secret_access_key')
        self.aws_security_token = self.get_option('aws_security_token')

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            session = botocore.session.get_session()
            if session.get_credentials() is not None:
                self.aws_access_key_id = session.get_credentials().access_key
                self.aws_secret_access_key = session.get_credentials().secret_key
                self.aws_security_token = session.get_credentials().token

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            raise AnsibleError("Insufficient boto credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith('.clints.yml') or path.endswith('.clints.yaml'):
                return True
        display.debug("clint inventory filename must end with '*.clints.yml' or '*.clints.yaml'")
        return False

    def _get_query_options(self, config_data):
        '''
            :param config_data: contents of the inventory config file
            :return A list of regions to query,
                    a list of boto3 filter dicts,
                    a list of possible hostnames in order of preference
                    a boolean to indicate whether to fail on permission errors
        '''
        options = {'regions': {'type_to_be': list, 'value': config_data.get('regions', [])}}

        # validate the options
        for name in options:
            options[name]['value'] = self._validate_option(name, options[name]['type_to_be'], options[name]['value'])

        return options['regions']['value']

    def _validate_option(self, name, desired_type, option_value):
        '''
            :param name: the option name
            :param desired_type: the class the option needs to be
            :param option: the value the user has provided
            :return The option of the correct class
        '''

        if isinstance(option_value, string_types) and desired_type == list:
            option_value = [option_value]

        if option_value is None:
            option_value = desired_type()

        if not isinstance(option_value, desired_type):
            raise AnsibleParserError("The option %s (%s) must be a %s" % (name, option_value, desired_type))

        return option_value

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._read_config_data(path)
        self._set_credentials()

        # get user specifications
        regions = self._get_query_options(config_data)

        self.inventory.add_group('clint_ios')
        self.inventory.add_child('all', 'clint_ios')
        self.inventory.add_group('clint_ssh')
        self.inventory.add_child('all', 'clint_ssh')

        for ec2, ecs, region in self._boto3_conn(regions):
            container_host_ips = {}
            use_clusters = ecs.describe_clusters(
                clusters=[
                    a for a in ecs.list_clusters()['clusterArns']
                    if 'static-ecs-cluster' in a
                ])['clusters']

            for cluster in use_clusters:
                cluster_name = cluster['clusterName']
                all_tasks = list(ecs.get_paginator('list_tasks').paginate(cluster=cluster_name).search('taskArns[]'))
                for i in range(0, len(all_tasks), 50):
                    running = [t for t in ecs.describe_tasks(tasks=all_tasks[i:i+50], cluster=cluster_name)['tasks'] if t['lastStatus'] == 'RUNNING']
                    for task in running:
                        if task['containerInstanceArn'] not in container_host_ips:
                            instance_id = ecs.describe_container_instances(cluster=cluster_name, containerInstances=[task['containerInstanceArn']])['containerInstances'][0]['ec2InstanceId']
                            inst_dns = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['PublicDnsName']
                            container_host_ips[task['containerInstanceArn']] = inst_dns
                        hostname = task['taskArn'].split('/')[-1].replace('-', '')
                        if 'ssh-target' in task['group']:
                            self.inventory.add_host(hostname, group='clint_ssh')
                        if 'ios-target' in task['group']:
                            self.inventory.add_host(hostname, group='clint_ios')
                        self.inventory.set_variable(hostname, 'ansible_host', container_host_ips[task['containerInstanceArn']])
                        self.inventory.set_variable(hostname, 'ansible_user', 'root')
                        self.inventory.set_variable(hostname, 'ansible_ssh_port', task['containers'][0]['networkBindings'][0]['hostPort'])
