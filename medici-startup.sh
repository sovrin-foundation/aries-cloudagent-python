#!/bin/bash

NGROK_NAME=${NGROK_NAME:-ngrok}

echo "ngrok end point [$NGROK_NAME]"

ENDPOINT=null
while [ $ENDPOINT = "null" ]
do
    echo "Fetching end point from ngrok service"
    ENDPOINT=$(curl --silent $NGROK_NAME:4040/api/tunnels | ./jq -r '.tunnels[0].public_url')

    if [ $ENDPOINT = "null" ]; then
        echo "ngrok not ready, sleeping 5 seconds...."
        sleep 5
    fi

done

echo "fetched end point [$ENDPOINT]"

aca-py start \
    -it http 0.0.0.0 3000 \
    -ot http \
    -e $ENDPOINT \
    --auto-accept-requests --auto-ping-connection \
    --auto-respond-credential-proposal --auto-respond-credential-offer --auto-respond-credential-request \
    --auto-respond-presentation-proposal --auto-respond-presentation-request --auto-verify-presentation \
    --invite --invite-role admin --invite-label MediciTrainingDockerAgent \
    --admin 0.0.0.0 3001 --admin-insecure-mode \
    --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/master/sovrin/pool_transactions_sandbox_genesis \
    --wallet-type indy
