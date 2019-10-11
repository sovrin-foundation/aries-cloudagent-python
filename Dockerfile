FROM bcgovimages/von-image:py36-1.11-1
ENV ENABLE_PTVSD 0

COPY ./requirements*.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

ADD ./aries_cloudagent ./aries_cloudagent
ADD ./bin ./bin
ADD ./README.md ./README.md
ADD ./setup.py ./setup.py

RUN pip3 install --no-cache-dir -e .[indy]

ENTRYPOINT ["/bin/bash", "-c", "aca-py start -it http 0.0.0.0 3001 -e http://host.docker.internal:3001 -ot http --auto-accept-requests --debug-connections --invite --invite-role admin --invite-label MediciTrainingDockerAgent --admin 0.0.0.0 3000 --admin-insecure-mode --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/master/sovrin/pool_transactions_sandbox_genesis --wallet-type indy", "--"]