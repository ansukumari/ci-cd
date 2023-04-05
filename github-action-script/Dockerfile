# Container image that runs your code
FROM python:3-alpine

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY deployCode.py /deployCode.py

RUN python -m pip install boto3
RUN pip install requests

# Code file to execute when the docker container starts up (`deployCode.py`)
ENTRYPOINT ["python3", "/deployCode.py"]
