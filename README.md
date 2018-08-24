# QA Scale Lab

[![Docker images at quay.io](https://quay.io/repository/ryansb/ansible-scale-test/status "Docker Repository on Quay")](https://quay.io/repository/ryansb/ansible-scale-test)

Creates an ECS cluster and an ASG of container hosts to SSH into for scale
testing Ansible playbooks and discovering performance issues. The
`list_clints.py` queries ECS and creates a static inventory file listing all
the CLINTs (Container Lightweight Inventory Numerous Targets) with the task
UUID as the inventory hostname.

# Usage

Copy `vars.template.yml` to `vars.yml` and fill in AWS profile and key.

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
