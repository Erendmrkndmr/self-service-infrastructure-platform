#!/bin/bash

KEY_NAME="erdemir-paris-key"              
KEY_DIR="./keys"                          
KEY_PATH="$KEY_DIR/$KEY_NAME.pem"         

# Terraform output IP
INSTANCE_IP=$(terraform output -raw instance_ip)

# SSH user
ANSIBLE_USER="ubuntu"                    

#.env
cat <<EOF > .env
INSTANCE_PUBLIC_IP=$INSTANCE_IP
ANSIBLE_USER=$ANSIBLE_USER
SSH_KEY_PATH=$KEY_PATH
EOF

echo ".env dosyası oluşturuldu:"
cat .env
