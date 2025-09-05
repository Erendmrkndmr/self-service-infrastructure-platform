#!/usr/bin/env bash
set -euo pipefail
# Kullanım: ./run_apply.sh <ENVIRONMENT> <INFRA_TYPE> <TTL_DAYS>

ENVIRONMENT="${1:-dev}"
INFRA_TYPE="${2:-web}"
TTL_DAYS="${3:-3}"

# (opsiyonel) Değişkenleri TF_VAR_* olarak geçmek istersen:
export TF_VAR_environment="$ENVIRONMENT"
export TF_VAR_infra_type="$INFRA_TYPE"
export TF_VAR_ttl_days="$TTL_DAYS"

cd "$(dirname "$0")"

terraform init -input=false -upgrade
terraform apply -auto-approve -input=false

# IP’yi JSON’dan çek
IP="$(terraform output -json instance_ip | tr -d '"' )"

# Güvenli çıktı (sadece IP)
echo "$IP"
