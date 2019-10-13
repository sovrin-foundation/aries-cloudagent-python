FROM bcgovimages/von-image:py36-1.11-1

RUN curl -L https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64 -o jq
RUN chmod +x jq

COPY ./requirements*.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

ADD ./aries_cloudagent ./aries_cloudagent
ADD ./bin ./bin
ADD ./README.md ./README.md
ADD ./setup.py ./setup.py

RUN pip3 install --no-cache-dir -e .[indy]

COPY medici-startup.sh startup.sh
ENTRYPOINT ["/bin/bash", "startup.sh"]
