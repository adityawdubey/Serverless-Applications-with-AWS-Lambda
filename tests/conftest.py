import os

# moto and boto3 require a region and credentials to exist, even when mocked.
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
# The handler reads TABLE_NAME at import time; give tests a fixed name.
os.environ.setdefault("TABLE_NAME", "Orders-test")
