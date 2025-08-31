from flask import Flask, render_template, request
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='frontend/templates')

# Jenkins bilgilerini al
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_API_TOKEN")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/provision', methods=['POST'])
def provision():
    provision_type = request.form.get('provision_type')
    env_name = request.form.get('environment_name')
    ttl_days = request.form.get('duration')

    print("FORM DATA:", request.form)
    print("Gelen RESOURCE:", provision_type)
    print("Gelen ENV_NAME:", env_name)
    print("Gelen TTL:", ttl_days)

    if provision_type == 'web':
        job_name = 'deploy-web'
    elif provision_type == 'db':
        job_name = 'deploy-db'
    else:
        return "Geçersiz provisioning tipi", 400

    # Jenkins bilgileri
    jenkins_url = os.getenv("JENKINS_URL")
    jenkins_user = os.getenv("JENKINS_USER")
    jenkins_token = os.getenv("JENKINS_API_TOKEN")

    job_url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
    params = {
        "ENV_NAME": env_name,
        "TTL_DAYS": ttl_days
    }

    response = requests.post(
        job_url,
        params=params,
        auth=(jenkins_user, jenkins_token)
    )

    if response.status_code == 201:
        return f"Provisioning triggered for {env_name}!", 200
    else:
        return f"Provisioning failed: {response.status_code} - {response.text}", 500

if __name__ == '__main__':
    app.run(port=int(os.getenv("FLASK_PORT", 5000)), debug=True)
