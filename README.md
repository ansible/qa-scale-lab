# QA Scale Lab

[![Docker images at quay.io](https://quay.io/repository/ryansb/ansible-scale-test/status "Docker Repository on Quay")](https://quay.io/repository/ryansb/ansible-scale-test)

Creates an ECS cluster and an ASG of container hosts to SSH into for scale
testing Ansible playbooks and discovering performance issues. The
`list_clints.py` queries ECS and creates a static inventory file listing all
the CLINTs (Container Lightweight Inventory Numerous Targets) with the task
UUID as the inventory hostname.

# Usage

Copy `vars.template.yml` to `vars.yml` and fill in AWS profile and key.

## deploy.yml

Creates a 3-node cluster and 2000 containers

## stop_cluster.yml

Turns the ASG down to 0 instances, leaving the rest of the infrastructure
untouched.

## destroy.yml

Deletes the instances, container registry, tasks, and VPC created in deploy.yml
