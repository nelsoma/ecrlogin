import os
import base64
import json
import boto3
from kubernetes import client, config

def main():
    aws_region = os.getenv("AWS_REGION")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    ecr_registry = os.getenv("ECR_REGISTRY")
    ecr_secret_name = os.getenv("ECR_SECRET_NAME")
    namespace = "default"

    if not all([aws_region, aws_access_key_id, aws_secret_access_key, ecr_registry, ecr_secret_name]):
        raise Exception("One or more required environment variables are missing.")

    # Get ECR login password via AWS API
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    ecr = session.client('ecr')
    token = ecr.get_authorization_token()
    auth_data = token['authorizationData'][0]
    auth_token = auth_data['authorizationToken']
    decoded_token = base64.b64decode(auth_token).decode('utf-8')
    username, password = decoded_token.split(':')

    # Prepare Docker config JSON
    docker_config = {
        "auths": {
            ecr_registry: {
                "username": username,
                "password": password,
                "auth": base64.b64encode(f"{username}:{password}".encode()).decode()
            }
        }
    }
    docker_config_json = json.dumps(docker_config)

    # Load Kubernetes config (in-cluster or local)
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    v1 = client.CoreV1Api()
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=ecr_secret_name, namespace=namespace),
        type="kubernetes.io/dockerconfigjson",
        data={".dockerconfigjson": base64.b64encode(docker_config_json.encode()).decode()}
    )

    # Create or replace the secret
    try:
        v1.create_namespaced_secret(namespace=namespace, body=secret)
        print(f"Secret {ecr_secret_name} created successfully in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            v1.replace_namespaced_secret(name=ecr_secret_name, namespace=namespace, body=secret)
            print(f"Secret {ecr_secret_name} replaced successfully in namespace {namespace}")
        else:
            raise

if __name__ == "__main__":
    main()