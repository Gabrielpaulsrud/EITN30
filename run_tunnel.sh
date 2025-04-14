#!/bin/bash

# Activate the virtual environment
source .env/bin/activate

# Run the script with sudo (only for TUN access)
sudo env "PATH=$PATH" "VIRTUAL_ENV=$VIRTUAL_ENV" python3 nrf_tunnel.py "$1"
