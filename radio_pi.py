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


def play_in_namespace(stream_url):

    curl_proc = subprocess.Popen(
        ["ip", "netns", "exec", "ns-client", "--compressed", "-L", "curl", "-s", stream_url],
        stdout=subprocess.PIPE
    )

    # Skicka utdata från curl direkt in i mpv via stdin
    mpv_proc = subprocess.run(
        subprocess.run(["mpv", "--no-cache", "--no-video", "--", "-"], stdin=curl_proc.stdout)
    )

    curl_proc.stdout.close()  # Viktigt: låt curl stänga sig själv när mpv är klar
    curl_proc.wait()

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



            # if index < 0 or index >= len(channels):
            #     choice = input("Ogiltigt val. Välj en ny kanal eller avsluta med 'q'").strip()
            #     continue

            if 0 <= index <= len(channels):
                stream_url = channels[index]['liveaudio']['url']
                channel_name = channels[index]['name']
                print(f"\nSpelar {channel_name}...\n")
                    
            
                print(stream_url)

                #     # mpv_cmd = [
                #     #     "sudo", "ip", "netns", "exec", "ns-client",
                #     #     "mpv", "--no-video", stream_url
                #     # ]

                #     # mpv_process = subprocess.run(mpv_cmd)

                #     play_in_namespace(stream_url)

                #     print(f"Channel {channel_name} has finished playing.\n")
                #     # # Wait for mpv to finish

                if stream_url.endswith('.mp3') and '-lo' not in stream_url:
                    stream_url = stream_url.replace('.mp3', '-lo.mp3')                
                stream_url = stream_url.replace("https://", "http://")
                
                subprocess.run(["mpv", 
                                "--no-video",
                                "--cache=yes",
                                "--cache-secs=60", 
                                "--demuxer-max-bytes=200M",   # Tillåt att 50MB laddas in
                                "--demuxer-readahead-secs=120",      # Större intern ljudbuffert
                                "--msg-level=ao=warn", stream_url])

                # curl_proc = subprocess.Popen(
                #     ["ip", "netns", "exec", "ns-client",  "curl","-L", "-s", stream_url],
                #     stdout=subprocess.PIPE
                # )

                # mpv_cmd = [
                #         "sudo", "ip", "netns", "exec", "ns-client",
                #         "mpv", "--no-video", stream_url
                #     ]

                # mpv_process = subprocess.run(mpv_cmd)


                # Skicka utdata från curl direkt in i mpv via stdin
                # mpv_proc = subprocess.run(
                #     ["mpv", "--no-cache", "--no-video", "-"],
                #     stdin=curl_proc.stdout
                # )

                # curl_proc.stdout.close()
                # curl_proc.wait()
            else :
                choice = input("Ogiltigt val. Välj en ny kanal eller avsluta med 'q'").strip()
                continue
            
        
        except ValueError:
            print("Du måste ange ett nummer.")
        
        choice = input("Välj kanal (nummer) eller avsluta med 'q': ").strip()
        

    print("Avslutar Radio Pi")
   
    
if __name__ == "__main__":
    main()
