#!/bin/bash

# Hämta SR-kanaler i JSON-format
response=$(curl -s "https://api.sr.se/api/v2/channels?format=json")

# Loopar genom varje kanal och skriver ut namn, tagline och stream-URL
echo "Tillgängliga Sveriges Radio-kanaler:"
echo "--------------------------------------"

echo "$response" | jq -r '.channels[] | 
    "\(.name)\nTagline: \(.tagline)\nStream: \(.liveaudio.url)\n---"'
