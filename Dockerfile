FROM centos:7

RUN yum -y update && \
    yum -y install openssh-server openssh-clients passwd curl && \
    yum clean all

RUN mkdir /var/run/sshd

RUN echo -e AnsibleFestIsBestFest | (passwd --stdin root)
RUN ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N ''
RUN ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key -N ''
RUN ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N ''
RUN ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ''

ENTRYPOINT ["/usr/sbin/sshd", "-D"]
EXPOSE 22
