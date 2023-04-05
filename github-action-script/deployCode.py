""" 
Sample command to run the script:
    python3 deployCode.py \
    -a xxxx \
    -k xxxx \
    --reg us-east-1 \
    --app web-server \
    -r <organization-name>/<repo-name> \
    -c xxx \
    -u Ansu \
    --ref v4.02 \
    --run 1234567890
"""

import boto3
import time
import sys
import argparse
import requests
from datetime import datetime

parser=argparse.ArgumentParser()

# Arguments needed to be passed to run this script:
parser.add_argument('--accessID', '-a', help='AWS Access Key ID')
parser.add_argument('--secretKey', '-k', help='AWS Secret Access Key')
parser.add_argument('--reg', help='AWS Region')
parser.add_argument('--app', help='AWS CodeDeploy Application')
parser.add_argument('--repo', '-r', help='Github Repository Name')
parser.add_argument('--commitID', '-c', help='The commit ID that needs to be deployed on the servers')
parser.add_argument('--user', '-u', help='Github User who triggered the workflow')
parser.add_argument('--ref', help='The branch or tag name that triggered the workflow run')
parser.add_argument('--run', help='A unique number for each workflow run within a repository.')

args=parser.parse_args()

client = boto3.client('codedeploy', aws_access_key_id=args.accessID, aws_secret_access_key=args.secretKey, region_name=args.reg)

app = args.app
dp_groups = client.list_deployment_groups(applicationName=app)['deploymentGroups']

revision = {
    'revisionType': 'GitHub',
    'gitHubLocation': {
        'repository': args.repo,
        'commitId': args.commitID
    }
}


# Setup to send notification alerts via POST request
deployments = []
error_msg = []

alert = {
    'startMsg': "A deployment has been triggered for *" + app + "* by *" + args.user + "* with Tag ID: `" + args.ref + "`",
    'successMsg': "*" + app + "* `" + args.ref + "` deployment *succeeded*.",
    'failureMsg': "*" + app + "* `" + args.ref + "` deployment *failed* on following deployment group(s).",
    'errorMsg': error_msg
}

if app == 'web-server':
    # Send POST request to Slack for deployment start
    requests.post('https://hooks.slack.com/services/XXXX/XXXX/xxxx', json={
        "attachments": [
            {
                "mrkdwn_in": ["text"],
                "title": "Deployment created",
                "title_link": "https://github.com/<organization-name>/<repo-name>/actions/runs/" + args.run,
                "text": alert['startMsg']
            }
        ]
    })

    # Send POST request to New Relic for deployment start
    requests.post('https://api.newrelic.com/v2/applications/123456789/deployments.json', headers={"Api-Key":"XXXX-XXXXXXXX"},  json={
    "deployment": {
        "revision": args.run + "|" + args.ref,
        "description": alert['startMsg'],
        "user": args.user,
        "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') # str((datetime.datetime.utcnow() - datetime.timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    }
    })
    
    
# Create AWS deployments for all deployment groups of the application passed in args.app
for group in dp_groups:
    deployment = client.create_deployment(applicationName=app, deploymentGroupName=group, revision=revision)

    dep_status = 'created'
    while dep_status != 'Failed' and dep_status != 'Succeeded': 
        print('waiting', dep_status)
        time.sleep(2)
        dep_status = client.get_deployment(deploymentId=deployment['deploymentId'])['deploymentInfo']['status']

    if dep_status == 'Failed': error_msg.append({
        "value": "✦ " + group + " - <https://us-east-1.console.aws.amazon.com/codesuite/codedeploy/deployments/" + deployment['deploymentId'] + "?region=us-east-1|" + deployment['deploymentId'] + ">", 
        "short": False
    })
    
    
# Send deployment completion status notification on Slack
if error_msg: 
    requests.post('https://hooks.slack.com/services/XXXX/XXXX/xxxx', json={
        "attachments": [
            {
                "mrkdwn_in": ["text"],
                "color": "danger",
                "title": "Deployment failed",
                "title_link": "https://github.com/<organization-name>/<repo-name>/actions/runs/" + args.run,
                "text": alert['failureMsg'],
                "fields": alert['errorMsg']
            }
        ]
    })
    sys.exit(1)
elif app == 'prod-backend':
    requests.post('https://hooks.slack.com/services/XXXX/XXXX/xxxx', json={
        "attachments": [
            {
                "mrkdwn_in": ["text"],
                "color": "good",
                "title": "Deployment succeeded",
                "title_link": "https://github.com/<organization-name>/<repo-name>/actions/runs/" + args.run,
                "text": alert['successMsg']
            }
        ]  
    })
        
