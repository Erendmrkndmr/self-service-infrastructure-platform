import os
import json
import ipaddress
import shlex
from datetime import datetime, timedelta, timezone
from subprocess import run as runproc, CalledProcessError, PIPE

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests

# .env yükle
load_dotenv()

app = Flask(__name__, template_folder='frontend/templates')

# Jenkins bilgileri
JENKINS_URL   = os.getenv("JENKINS_URL")
JENKINS_USER  = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_API_TOKEN")

# Terraform ayarları
TF_DIR          = os.getenv("TF_DIR", os.path.join(os.getcwd(), "terraform"))
TF_OUTPUT_KEY   = os.getenv("TF_OUTPUT_KEY", "instance_ip")  # outputs.tf'daki isim
TF_DEFAULT_SIZE = os.getenv("TF_DEFAULT_SIZE", "small")

STATUS_PATH = os.path.join("status", "environments.json")
os.makedirs("status", exist_ok=True)
if not os.path.exists(STATUS_PATH):
    with open(STATUS_PATH, "w") as f:
        json.dump([], f, indent=2)

def _read_status():
    try:
        with open(STATUS_PATH) as f:
            return json.load(f)
    except Exception:
        return []

def _write_status(data):
    with open(STATUS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def _upsert_env(env_name, **fields):
    data = _read_status()
    now_iso = datetime.now(timezone.utc).isoformat()
    found = False
    for item in data:
        if item.get("env_name") == env_name:
            item.update(fields)
            item["updated_at"] = now_iso
            found = True
            break
    if not found:
        new_rec = {"env_name": env_name, "created_at": now_iso, "updated_at": now_iso}
        new_rec.update(fields)
        data.append(new_rec)
    _write_status(data)

def _sh(cmd_list, cwd=None):
    """ Subprocess çalıştırma; hata olursa stdout/stderr ile fail ettir. """
    try:
        p = runproc(cmd_list, cwd=cwd, text=True, stdout=PIPE, stderr=PIPE, check=True)
        return p.stdout.strip()
    except CalledProcessError as e:
        msg = f"cmd={' '.join(shlex.quote(c) for c in cmd_list)}\nexit={e.returncode}\nstdout={e.stdout}\nstderr={e.stderr}"
        raise RuntimeError(msg)

def run_terraform(env_name: str, template: str, size: str = TF_DEFAULT_SIZE) -> str:
    """
    terraform/ dizininde:
      - init
      - apply (-var=env_name, -var=template, -var=size)
      - output -raw <TF_OUTPUT_KEY>
    """
    if not os.path.isdir(TF_DIR):
        raise RuntimeError(f"Terraform directory not found: {TF_DIR}")

    _upsert_env(env_name, status="terraform_starting", last_message="Terraform init başlıyor...")

    _sh(["terraform", "init", "-input=false", "-upgrade"], cwd=TF_DIR)
    _upsert_env(env_name, status="terraform_init_done", last_message="Terraform init tamam.")

    _upsert_env(env_name, status="terraform_applying", last_message="Terraform apply çalışıyor...")
    _sh([
        "terraform", "apply", "-auto-approve", "-input=false",
        f"-var=env_name={env_name}",
        f"-var=template={template}",
        f"-var=size={size}"
    ], cwd=TF_DIR)
    _upsert_env(env_name, status="terraform_applied", last_message="Terraform apply tamam.")

    ip = _sh(["terraform", "output", "-raw", TF_OUTPUT_KEY], cwd=TF_DIR).strip()
    try:
        ipaddress.ip_address(ip)
    except Exception:
        raise RuntimeError(f"Terraform output '{TF_OUTPUT_KEY}' geçersiz veya boş: '{ip}'")

    _upsert_env(env_name, status="terraform_done", public_ip=ip, last_message=f"EC2 hazır: {ip}")
    return ip

def _jenkins_build_with_params(job_name: str, params: dict) -> requests.Response:
    """
    Crumb alıp buildWithParameters çağırır.
    Başarılı kabul: 201 (Created), 200 (bazı proxy’lerde), 302 (queue).
    """
    base = (JENKINS_URL or "").rstrip("/")
    if not base or not JENKINS_USER or not JENKINS_TOKEN:
        raise RuntimeError("Jenkins bilgileri eksik (JENKINS_URL / JENKINS_USER / JENKINS_API_TOKEN).")

    crumb_url = f"{base}/crumbIssuer/api/json"
    r = requests.get(crumb_url, auth=(JENKINS_USER, JENKINS_TOKEN), timeout=15)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Jenkins crumb alınamadı: {r.status_code} - {r.text[:200]}")
    cj = r.json()
    headers = {cj.get("crumbRequestField", "Jenkins-Crumb"): cj.get("crumb")}

    job_url = f"{base}/job/{job_name}/buildWithParameters"
    resp = requests.post(job_url, data=params, headers=headers,
                         auth=(JENKINS_USER, JENKINS_TOKEN),
                         timeout=30, allow_redirects=False)
    return resp

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status/<env_name>')
def status(env_name):
    data = _read_status()
    for r in data:
        if r.get("env_name") == env_name:
            return jsonify(r), 200
    return jsonify({"error": "not found"}), 404

@app.route('/provision', methods=['POST'])
def provision():
    provision_type = request.form.get('provision_type')  # 'web' | 'db'
    env_name       = request.form.get('env_name') or 'test'
    ttl_days       = request.form.get('duration') or '3'

    if provision_type not in ("web", "db"):
        return "Geçersiz provisioning tipi", 400

    size = TF_DEFAULT_SIZE
    expires_at = (datetime.now(timezone.utc) + timedelta(days=int(ttl_days))).isoformat()

    _upsert_env(
        env_name,
        template=provision_type,
        size=size,
        expires_at=expires_at,
        status="starting",
        last_message="Terraform başlatılıyor..."
    )

    # 1) Terraform (Flask tarafında)
    try:
        ip = run_terraform(env_name, provision_type, size)
    except Exception as e:
        _upsert_env(env_name, status="failed", last_message=f"Terraform hata: {e}")
        return f"Terraform hata: {e}", 500

    # 2) Jenkins deploy job adı
    job_name = "deploy-web" if provision_type == "web" else "deploy-db"

    # 3) Jenkins tetikle (crumb ile)
    params = {
        "HOST_IP": ip,
        "ENVIRONMENT": env_name,
        "USERNAME": "self-service-portal",
        "DELETE_AFTER_DAYS": ttl_days
    }

    _upsert_env(env_name, status="jenkins_trigger", last_message=f"Jenkins tetikleniyor: {job_name}")
    try:
        resp = _jenkins_build_with_params(job_name, params)
        if resp.status_code not in (200, 201, 302):
            _upsert_env(env_name, status="failed",
                        last_message=f"Jenkins hata: {resp.status_code} - {resp.text[:200]}")
            return f"Jenkins trigger başarısız: {resp.status_code} - {resp.text}", 500
    except Exception as e:
        _upsert_env(env_name, status="failed", last_message=f"Jenkins istek hata: {e}")
        return f"Jenkins istek hata: {e}", 500

    _upsert_env(env_name, status="running", last_message=f"Jenkins çalışıyor (IP: {ip})", public_ip=ip)
    return f"Provisioning triggered for {env_name}! (IP: {ip})", 200

if __name__ == '__main__':
    app.run(port=int(os.getenv("FLASK_PORT", 5000)), debug=True)
