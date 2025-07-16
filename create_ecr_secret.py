import os
import base64
import json
import boto3
from kubernetes import client, config
import logging

def main():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    aws_region = os.getenv("AWS_REGION")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    ecr_registry = os.getenv("ECR_REGISTRY")
    ecr_secret_name = os.getenv("ECR_SECRET_NAME")
    namespace = "default"

    logging.basicConfig(level=getattr(logging, log_level, logging.DEBUG))
    logger = logging.getLogger(__name__)

    logger.debug(f"AWS_REGION: {aws_region}")
    logger.debug(f"ECR_REGISTRY: {ecr_registry}")
    logger.debug(f"ECR_SECRET_NAME: {ecr_secret_name}")
    logger.debug(f"NAMESPACE: {namespace}")

    if not all([aws_region, aws_access_key_id, aws_secret_access_key, ecr_registry, ecr_secret_name]):
        logger.error("One or more required environment variables are missing.")
        raise Exception("One or more required environment variables are missing.")

    # Get ECR login password via AWS API
    logger.debug("Creating boto3 session for ECR.")
    session = boto3.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    ecr = session.client('ecr')
    logger.debug("Requesting ECR authorization token.")
    token = ecr.get_authorization_token()
    auth_data = token['authorizationData'][0]
    auth_token = auth_data['authorizationToken']
    decoded_token = base64.b64decode(auth_token).decode('utf-8')
    username, password = decoded_token.split(':')
    logger.debug(f"Decoded ECR username: {username}")

    # Prepare Docker config JSON
    logger.debug("Preparing Docker config JSON.")
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
    logger.debug(f"Docker config JSON: {docker_config_json}")

    # Load Kubernetes config (in-cluster or local)
    try:
        logger.debug("Trying to load in-cluster Kubernetes config.")
        config.load_incluster_config()
        logger.debug("Loaded in-cluster Kubernetes config.")
    except Exception as e:
        logger.debug(f"In-cluster config failed: {e}. Trying local kube config.")
        config.load_kube_config()
        logger.debug("Loaded local kube config.")

    v1 = client.CoreV1Api()
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(name=ecr_secret_name, namespace=namespace),
        type="kubernetes.io/dockerconfigjson",
        data={".dockerconfigjson": base64.b64encode(docker_config_json.encode()).decode()}
    )

    # Create or replace the secret
    try:
        logger.debug(f"Creating secret {ecr_secret_name} in namespace {namespace}.")
        v1.create_namespaced_secret(namespace=namespace, body=secret)
        logger.info(f"Secret {ecr_secret_name} created successfully in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            logger.debug(f"Secret {ecr_secret_name} already exists. Replacing it.")
            v1.replace_namespaced_secret(name=ecr_secret_name, namespace=namespace, body=secret)
            logger.info(f"Secret {ecr_secret_name} replaced successfully in namespace {namespace}")
        else:
            logger.error(f"Failed to create or replace secret: {e}")
            raise

if __name__ == "__main__":
    main()