# QA Scale Lab

Creates an ECS cluster and an ASG of container hosts to SSH into for scale
testing Ansible playbooks and discovering performance issues.

# Usage

Copy `vars.template.yml` to `vars.yml` and fill in AWS profile and key.

## deploy.yml

Creates a 3-node cluster and 2000 containers

## stop_cluster.yml

Turns the ASG down to 0 instances, leaving the rest of the infrastructure
untouched.

## destroy.yml

Deletes the instances, container registry, tasks, and VPC created in deploy.yml
