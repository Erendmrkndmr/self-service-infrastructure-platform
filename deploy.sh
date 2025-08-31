#!/bin/bash

echo "➡ Terraform apply başlatılıyor..."
cd terraform
terraform init -input=false
terraform apply -auto-approve -input=false

# Terraform çıktısından EC2 IP alınır
EC2_HOST=$(terraform output -raw instance_ip)
echo "✅ EC2 oluşturuldu. IP: $EC2_HOST"
cd ..

# .env dosyasını güncelle (veya oluştur)
echo "EC2_HOST=$EC2_HOST" > .env

# SSH ile bağlantı kurularak Jenkins kurulumu yapılır
echo "➡ EC2'ye Jenkins kurulumu başlatılıyor..."
scp -i ./keys/erdemir-paris-key.pem -o StrictHostKeyChecking=no -r ./jenkins ubuntu@$EC2_HOST:~/jenkins

ssh -i ./keys/erdemir-paris-key.pem -o StrictHostKeyChecking=no ubuntu@$EC2_HOST << EOF
  cd ~/jenkins
  docker build -t selfservice-jenkins .
  docker stop selfservice-jenkins 2>/dev/null || true
  docker rm selfservice-jenkins 2>/dev/null || true
  docker run -d -p 8080:8080 --name selfservice-jenkins selfservice-jenkins
EOF

echo "✅ Jenkins kurulumu tamamlandı. Tarayıcıdan erişebilirsiniz: http://$EC2_HOST:8080"
