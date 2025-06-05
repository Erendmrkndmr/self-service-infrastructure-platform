from flask import Flask, render_template, request
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # .env dosyasını yükle

app = Flask(__name__)

# Environment variable'ları oku
JENKINS_URL = os.getenv("JENKINS_URL")
JENKINS_USER = os.getenv("JENKINS_USER")
JENKINS_TOKEN = os.getenv("JENKINS_TOKEN")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/provision', methods=['POST'])
def provision():
    template = request.form['template']
    env_name = request.form['env_name']
    size = request.form['size']
    expire_date = request.form['expire_date']

    response = requests.get(
        f"{JENKINS_URL}/job/provision-environment/buildWithParameters",
        auth=(JENKINS_USER, JENKINS_TOKEN),
        params={
            "TEMPLATE": template,
            "ENV_NAME": env_name,
            "SIZE": size
        }
    )

    new_env = {
        "env_name": env_name,
        "template": template,
        "size": size,
        "expire_date": expire_date,
        "status": "triggered",
        "created_at": datetime.now().isoformat()
    }

    with open("../status/environments.json", "r+") as f:
        try:
            data = json.load(f)
        except:
            data = []
        data.append(new_env)
        f.seek(0)
        json.dump(data, f, indent=2)

    return f"Provisioning triggered for {env_name}!"

if __name__ == '__main__':
    app.run(port=int(os.getenv("FLASK_PORT", 5000)), debug=True)
