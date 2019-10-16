FROM bcgovimages/von-image:py36-1.11-1

COPY ./requirements*.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

ADD ./aries_cloudagent ./aries_cloudagent
ADD ./bin ./bin
ADD ./README.md ./README.md
ADD ./setup.py ./setup.py

RUN pip3 install --no-cache-dir -e .[indy]

USER root
ADD https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 ./jq
RUN chmod +x ./jq
COPY medici-startup.sh startup.sh
RUN chmod +x ./startup.sh
COPY ngrok-wait.sh wait.sh
RUN chmod +x ./wait.sh

USER $user

CMD ./wait.sh ./startup.sh
