import boto3
import json
from pprint import pprint
sess = boto3.Session(region_name='us-east-2')
ecs = sess.client('ecs')
ec2 = sess.client('ec2')

use_cluster = ecs.describe_clusters(clusters=ecs.list_clusters()['clusterArns'])['clusters'][0]
cluster_name = use_cluster['clusterName']

container_host_ips = {}

all_tasks = list(ecs.get_paginator('list_tasks').paginate(cluster=cluster_name).search('taskArns[]'))

for i in range(0, len(all_tasks), 50):
    running = [t for t in ecs.describe_tasks(tasks=all_tasks[i:i+50], cluster=cluster_name)['tasks'] if t['lastStatus'] == 'RUNNING']
    for task in running:
        if task['containerInstanceArn'] not in container_host_ips:
            #pprint(task)
            instance_id = ecs.describe_container_instances(cluster=cluster_name, containerInstances=[task['containerInstanceArn']])['containerInstances'][0]['ec2InstanceId']
            #pprint(ecs.describe_container_instances(cluster=cluster_name, containerInstances=[task['containerInstanceArn']])['containerInstances'][0])
            inst_dns = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['PublicDnsName']
            container_host_ips[task['containerInstanceArn']] = inst_dns
        print ' '.join([
            task['taskArn'].split('/')[-1].replace('-', ''),
            'ansible_host=%s' % container_host_ips[task['containerInstanceArn']],
            'ansible_user=root',
            'ansible_ssh_port=%s' % task['containers'][0]['networkBindings'][0]['hostPort'],
            ])
