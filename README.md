# ecrlogin

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
