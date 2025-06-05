FROM jenkins/jenkins:lts

USER root

RUN apt-get update && apt-get install -y \
  python3-pip \
  ansible \
  sshpass

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt



COPY casc_configs /var/jenkins_home/casc_configs/
#COPY init.groovy.d /usr/share/jenkins/ref/init.groovy.d/

ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"