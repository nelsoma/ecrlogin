# ecrlogin

## Purpose

This project provides a simple utility to automate the creation and refreshing of a Kubernetes `docker-registry` secret using  ECR credentials.  
It retrieves ECR authentication tokens using AWS credentials from environment variables and creates or updates a Kubernetes secret, allowing Kubernetes workloads to securely pull images from private ECR repositories.

The Python script and example Kubernetes manifests allow ECR authentication from your Kubernetes environment.

## Local Usage
Setup venv:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Set environment variables, eg:
```bash
export AWS_REGION=us-west-2
export AWS_ACCESS_KEY_ID=AKIAASDFSEF12SASDEGA
export AWS_SECRET_ACCESS_KEY=SDFwsdfwwewEFTHeahwgweWWEFwetWEvWEhehtrH
export ECR_REGISTRY=111111111111.dkr.ecr.us-west-2.amazonaws.com
export ECR_SECRET_NAME=ansible-ecr-login
```

Run:
```bash
pip3 install -r requirements.txt
python3 create_ecr_secret.py
```

## Setup K8s
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ecr-refresher-sa
---
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: ecr-refresher-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "create", "delete", "patch", "update"]
- apiGroups: [""]
  resources: ["serviceaccounts"]
  verbs: ["get", "patch"]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: ecr-refresher-rolebinding
subjects:
  - kind: ServiceAccount
    name: ecr-refresher-sa
roleRef:
  kind: Role
  name: ecr-refresher-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ecr-credential-refresher
spec:
  schedule: "0 */6 * * *" # Runs every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: ecr-refresher-sa
          imagePullSecrets:
          - name: aws-ecr-registry
          containers:
          - name: ecr-refresher
            image: 222222222222.dkr.ecr.us-west-2.amazonaws.com/ecrlogin:latest # Replace with this image
            imagePullPolicy: IfNotPresent
            env:
              - name: AWS_REGION
                value: us-west-2 # Replace with your region
              - name: AWS_ACCESS_KEY_ID
                valueFrom:
                  secretKeyRef:
                    name: aws-ecr-read # Replace with your secret name
                    key: aws_access_key_id
              - name: AWS_SECRET_ACCESS_KEY
                valueFrom:
                  secretKeyRef:
                    name: aws-ecr-read # Replace with your secret name
                    key: aws_secret_access_key
              - name: ECR_REGISTRY
                value: 222222222222.dkr.ecr.us-west-2.amazonaws.com # Replace with your registry
              - name: ECR_SECRET_NAME
                value: aws-ecr-registry # Replace with the secret name you want to update
          restartPolicy: OnFailure
```