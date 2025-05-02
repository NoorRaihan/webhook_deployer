import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import yaml
import os
from cerberus import Validator
from typing import Optional
import subprocess

app = FastAPI()
apps = {}
validation_scheme = {
    'application': {
        'type': 'dict',
        'valuesrules': {
            'type': 'dict',
            'schema': {
                'deploy-command': {
                    'type': 'list',
                    'schema': {
                        'type': 'string'
                    }
                }
            }
        }
    }
}
  

def init_yaml(filepath: str):
    try:
        with open(filepath, "r") as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Failed to read {filepath} : {e}")
        exit(-1)

def init_config():
    global apps
    file_config = os.getenv("WEBHOOK_CONFIG_FILE", default=os.path.join(os.getcwd(),"deploy.yaml"))

    if not os.getenv("APP_TOKEN"):
        print("Secret token not configured")
        exit(-1)

    configs = init_yaml(file_config)
    if not configs:
        print(f"Config is none")
        exit(-1)
    
    validator = Validator(validation_scheme)
    if not validator.validate(configs):
        print(validator.errors)
        exit(-1)
    
    apps = configs.get("application")

def validate_token(authorization: Optional[str] = Header(None)):
    if authorization is None or authorization != "Bearer " + os.getenv("WEBHOOK_CONFIG_FILE"):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return authorization

def replace_placeholders(arr, **kwargs):
    result = []
    pattern = re.compile(r'\$([a-zA-Z_]\w*)')

    for item in arr:
        if isinstance(item, str):
            def replacer(match):
                key = match.group(1)
                return str(kwargs.get(key, match.group(0)))
            new_item = pattern.sub(replacer, item)
            result.append(new_item)
        else:
            result.append(item)
    return result

@app.post("/webhook/deploy/{app_id}")
async def deploy_app(app_id: str, request: Request, token: str = Depends(validate_token)):
    data = await request.json()
    print(data)

    if data.get("type") != "PUSH_ARTIFACT":
        return JSONResponse(status_code=200, content={"message": "ignored"})
    
    resources = data.get("event_data").get("resources")[0]

    if resources.get("tag") != "latest":
        return JSONResponse(status_code=200, content={"message": "tag not latest, ignored"})
    
    kwargs = {
        "TAG" : "latest",
        "REGISTRY_URL": resources.get("resource_url")
    }

    if not app_id:
        return JSONResponse(status_code=500, content={"message": "app_id is required"})
    
    if not apps.get(app_id):
        return JSONResponse(status_code=404, content={"message": f"{app_id} does not found in the configuration"})
    
    result = run_deploy_command(replace_placeholders(apps.get(app_id).get("deploy-command"), **kwargs))
    if not result or result.returncode != 0:
        return JSONResponse(status_code=500, content={"message": f"Failed to trigger deploy command for {app_id}"})
    
    return JSONResponse(status_code=200, content={"message": "success"})

def run_deploy_command(command):
    try:
        return subprocess.run(command, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("Command failed:", e.stderr)
        return None

if __name__ == "__main__":
    init_config()
    uvicorn.run(app, host="0.0.0.0", port=8080)