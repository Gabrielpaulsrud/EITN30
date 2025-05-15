#!/bin/bash
set -e

NS="ns-client"
USER_ID=$(id -u)
RUNTIME_DIR="/run/user/$USER_ID"
PULSE_SOCKET="$RUNTIME_DIR/pulse"
SCRIPT_PATH="$(dirname "$(realpath "$0")")/radio_pi.py"

# Kontrollera att scriptet finns
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Kunde inte hitta radio_script.py"
    exit 1
fi

# Kontrollera att namespace existerar
if ! ip netns list | grep -q "$NS"; then
    echo "❌ Namespace '$NS' finns inte. Starta ert tunnelprogram först."
    exit 1
fi

# Bind-mount /dev/snd
echo "🎧 Mountar /dev/snd in i namespace"
sudo mount --bind /dev/snd /var/run/netns/$NS/dev/snd || true

# Bind-mount PulseAudio UNIX socket
if [ -d "$PULSE_SOCKET" ]; then
    echo "🔊 Mountar PulseAudio-socket"
    sudo mkdir -p /var/run/netns/$NS$PULSE_SOCKET
    sudo mount --bind "$PULSE_SOCKET" "/var/run/netns/$NS$PULSE_SOCKET" || true
else
    echo "⚠️ PulseAudio socket hittades inte, fortsätter ändå"
fi

# Starta Python-script i namespace med PulseAudio-stöd
echo "🚀 Startar radio_script.py i '$NS' med ljud"
sudo ip netns exec $NS env \
    XDG_RUNTIME_DIR="$RUNTIME_DIR" \
    PULSE_SERVER="unix:$PULSE_SOCKET/native" \
    python3 "$SCRIPT_PATH"
