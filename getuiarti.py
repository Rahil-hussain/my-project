import os
import time
import uuid
from json import JSONDecodeError

import requests
from infrastructure.log import logger

get_env = os.environ.get

branch_name = get_env('MVRETAIL_BRANCH')
base_url = get_env('MCP_URL', 'https://dev-bastion-internal.mvretail.com')
if not branch_name:
    logger.error(f'no MVRETAIL_BRANCH env var value found.')
    exit(1)

payload = {
    "Action": "build.yml",
    "SourcePath": "main/javascript/react",
    "Repository": "MVRetail",
    "Branch": branch_name
}

build_url = f'{base_url}/buildArtifact'
headers = {'Content-Type': 'application/json'}

logger.info(f'requesting assets for branch {branch_name} from: {build_url}')
logger.info(f'using payload of: {payload}')

elapsed = 0
timeout = 60 * 15
increment = 10

response = requests.post(build_url, headers=headers, json=payload)
try:
    response_data = response.json()
except JSONDecodeError:
    logger.error(f'buildArtifact endpoint returned non json serializable response: {response.content}')
    exit(1)

completed = response_data.get('Status') in ['success', 'failed']

while not completed and elapsed < timeout:
    time.sleep(increment)
    elapsed += increment
    response = requests.post(build_url, headers=headers, json=payload)
    try:
        response_data = response.json()
    except JSONDecodeError:
        logger.error(f'buildArtifact endpoint returned non json serializable response: {response.content}')
        exit(1)
    completed = response_data.get('Status') in ['success', 'failed']

    if 'errors' in response_data:
        logger.error(f'error building assets for {branch_name}!  {response.status_code}:{response.text}')
        exit(1)

    logger.info(f'polling... {response.status_code}:{response.text}')

if not completed:
    logger.error(f'web ui assets not ready in {timeout / 60} min.')
    exit(1)

# otherwise, assume success and attempt to download the assets
logger.info('downloading assets...')
artifact_id = response_data.get('ID')
filename = f'{uuid.uuid4()}-{artifact_id}'
artifact_url = f'{base_url}/downloadArtifact?Repository=MVRetail&ID={artifact_id}'
artifact_response = requests.get(artifact_url, headers=headers)

# write asset zip data to file for other user to decompress
with open('assets.zip', 'wb') as file:
    for chunk in artifact_response.iter_content():
        file.write(chunk)
