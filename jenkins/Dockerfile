FROM jenkins/jenkins:lts

USER root


# Ansible yükle
RUN apt-get update && \
    apt-get install -y ansible


RUN chown -R jenkins:jenkins /var/jenkins_home
USER jenkins

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# ✅ Doğru yer
COPY casc_configs/jenkins.yaml /usr/share/jenkins/ref/casc_configs/jenkins.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc_configs/jenkins.yaml

COPY init.groovy.d /usr/share/jenkins/ref/init.groovy.d