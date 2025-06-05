#!/bin/bash

# .env
export $(grep -v '^#' .env | xargs)

mkdir -p ansible/inventory

# inventory.ini
cat <<EOF > ansible/inventory/inventory.ini
[web]
$INSTANCE_PUBLIC_IP ansible_user=$ANSIBLE_USER ansible_ssh_private_key_file=$SSH_KEY_PATH
EOF

echo "Inventory dosyası oluşturuldu: ansible/inventory/inventory.ini"
