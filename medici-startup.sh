ENDPOINT=$(curl --silent ngrok:4040/api/tunnels | ./jq -r '.tunnels[0].public_url')

aca-py start \
      -it http 0.0.0.0 3000 \
      -ot http \
      -e $ENDPOINT \
      --auto-accept-requests \
      --invite --invite-role admin --invite-label MediciTrainingDockerAgent \
      --admin 0.0.0.0 3001 --admin-insecure-mode \
      --genesis-url https://raw.githubusercontent.com/sovrin-foundation/sovrin/master/sovrin/pool_transactions_sandbox_genesis \
      --wallet-type indy
