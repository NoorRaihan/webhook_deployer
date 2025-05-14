# 🚀 FastAPI Webhook Deployer

A lightweight and secure **FastAPI** service that listens to container registry webhook events and executes custom deploy commands when specific conditions (like `PUSH_ARTIFACT`) are met.

Built for automating service deployments with minimal overhead, this deployer supports token-based authentication and environment-based configuration.

---

## 📦 Features

- ✅ Secure webhook with **Bearer token** authentication
- 🔁 Listens for `PUSH_ARTIFACT` events (e.g., from GitHub Container Registry, Harbor, etc.)
- 🔧 Executes custom **shell-based deploy commands**
- 🧠 Smart environment variable substitution in commands (e.g. `$TAG`, `$REGISTRY_URL`)
- ⚙️ Configuration driven via YAML
- 🐍 Built with FastAPI + Cerberus for validation

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/webhook-deployer.git
cd webhook-deployer
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Create your deploy.yaml config
Example:

```yaml
application:
  my-registry/my-app:
    deploy-command:
      - "sh"
      - "-c"
      - "docker pull $REGISTRY_URL && docker stop my-app && docker rm my-app && docker run -d --name my-app $REGISTRY_URL"
```

🔐 Environment Variables
Variable	Required	Description
WEBHOOK_APP_TOKEN	✅	Bearer token used for authenticating requests
WEBHOOK_CONFIG_FILE	❌	Path to the deploy config YAML (default: ./deploy.yaml)

You can export these in your shell or set them via a .env file.

Example:
```
export WEBHOOK_APP_TOKEN="supersecrettoken"
export WEBHOOK_CONFIG_FILE="/etc/webhook/deploy.yaml"
```

📮 Webhook Endpoint
POST /webhook/deploy
Headers:
```http
Authorization: Bearer <WEBHOOK_APP_TOKEN>
Content-Type: application/json
```

Example Payload:
```json
{
  "type": "PUSH_ARTIFACT",
  "event_data": {
    "repository": {
      "repo_full_name": "my-registry/my-app"
    },
    "resources": [
      {
        "tag": "latest",
        "resource_url": "my-registry/my-app:latest"
      }
    ]
  }
}
```
🔐 Only events of type PUSH_ARTIFACT are processed.

🧠 How It Works
1. Validates token using Bearer authentication.
2. Parses the incoming JSON for PUSH_ARTIFACT.
3. Looks up the associated application in deploy.yaml.
4. Substitutes placeholders like $TAG and $REGISTRY_URL.
5. Executes the shell command for deployment.
6. Returns a success or failure response.

🧪 Example Test with curl
```bash
curl -X POST http://localhost:8080/webhook/deploy \
  -H "Authorization: Bearer supersecrettoken" \
  -H "Content-Type: application/json" \
  -d @sample_payload.json
```

🍗 Fun Fact
This webhook was originally written in a burst of productivity (and chicken nugget cravings) to automate deployment flows for PvC CTF infrastructure. ❤️ DevOps with flavor.
