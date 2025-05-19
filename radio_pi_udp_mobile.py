import socket
import time
import subprocess
import requests
import subprocess
import os
import tempfile

import requests
import subprocess
import os
import tempfile

def fetch_channels():
    url = "https://api.sr.se/api/v2/channels?format=json&size=100"
    response = requests.get(url)
    data = response.json()
    return data['channels']

def show_menu(channels):
    print("\nTillgängliga Sveriges Radio-kanaler:\n")
    for i, ch in enumerate(channels):
        print(f"{i+1}. {ch['name']} - {ch['tagline']} \n")
    print()


def send_channel_to_base(stream_url, base_ip="11.11.11.1", port=5002):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(stream_url.encode(), (base_ip, port))

def listen_with_ffplay(port=12346,base_ip="11.11.11.1" ):
    print(f"\nStartar ffplay för att ta emot ljud via UDP på port {port}...\n")
    subprocess.run(["ffplay", "-nodisp", "-exitonkeydown", f"udp://{base_ip}:{port}"])

def main():
    channels = fetch_channels()
    current_process = None
    
    show_menu(channels)

    choice = input("Välj kanal (nummer) eller avsluta med 'q': ").strip()

    while choice != 'q':
        try:
            if not choice.isdigit():
                choice = input("Ogiltigt val. Välj en ny kanal eller avsluta med 'q'").strip()
                continue

            index = int(choice) - 1

            if 0 <= index <= len(channels):
                stream_url = channels[index]['liveaudio']['url']
                channel_name = channels[index]['name']
                print(f"\nSpelar {channel_name}...\n")
                    
            
                print(stream_url)

                send_channel_to_base(stream_url)  # Skickar URL till basstationen
                time.sleep(1)  # Vänta kort så basstationen hinner starta ffmpeg
                listen_with_ffplay()



            else :
                choice = input("Ogiltigt val. Välj en ny kanal eller avsluta med 'q'").strip()
                continue
            
        
        except ValueError:
            print("Du måste ange ett nummer.")
        
        choice = input("Välj kanal (nummer) eller avsluta med 'q': ").strip()
        

    print("Avslutar Radio Pi")
   
    
if __name__ == "__main__":
    main()
