# QA Scale Lab

[![Docker images at quay.io](https://quay.io/repository/ryansb/ansible-scale-test/status "Docker Repository on Quay")](https://quay.io/repository/ryansb/ansible-scale-test)

Creates an ECS cluster and an ASG of container hosts to SSH into for scale
testing Ansible playbooks and discovering performance issues. The
`./inventory/clints.py` inventory plugin queries ECS and creates inventory
hosts with all the CLINTs (Container Lightweight Inventory Numerous Targets)
with the task UUID as the inventory hostname.

# Usage

Copy `vars.template.yml` to `vars/vars.yml` and fill in AWS profile and (optionally)
an EC2 SSH key. The default instance type is m5.4xlarge, but c5.4xlarge and
t3.large are also supported.

To choose how many targets are created, set the `desired_targets` parameters
for the container types you need. By default, 2000 centos SSH containers are
created. The number of container hosts (m5.4xlarge) is calculated based on the
number of targets, so there's no need to change the autoscaling group
configuration manually.

## deploy.yml

Creates a host cluster and (by default) 2000 containers. To turn off the
cluster, run `deploy.yml` again with the numbers of `desired_hosts` set to
zero. This will delete all the containre hosts in the autoscaling group and
scale the ECS services to zero containers.

## destroy.yml

Deletes the instances, container registry, tasks, and VPC created in deploy.yml

## Custom Inventory Plugin

To SSH to all the fake hosts, you will need to use the included inventory
plugin that discovers running ECS tasks.

Here's a sample config for that inventory:

```
# in ./inventory/all.clints.yml
plugin: clints
regions:
  - us-east-2
boto_profile: YourProfileHere
```

To test that the plugin is working, you can run `ansible-inventory --list` and
there should be a long list of hosts with UUID-looking names. Once that's the
case, you can run any Ansible you like across the SSH hosts like this:

```
ansible clint_ssh -m ping
```

# Licensing

This repo is made available under the Apache 2.0 license. The `cfn/`
directory also contains Apache 2.0 licensed code courtesy of
[aws-cf-templates](https://github.com/widdix/aws-cf-templates).
