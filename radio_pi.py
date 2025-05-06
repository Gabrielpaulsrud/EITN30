import requests
import subprocess

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

            if 1 <= index <= len(channels):
                stream_url = channels[index]['liveaudio']['url']
                channel_name = channels[index]['name']
                print(f"\nSpelar {channel_name}...\n")
                subprocess.run(["mpv", stream_url])
            
            else:
                choice = input("Ogiltigt val. Välj en ny kanal eller avsluta med 'q'").strip()
                continue
        except ValueError:
            print("Du måste ange ett nummer.")
        
        choice = input("Välj kanal (nummer) eller avsluta med 'q': ").strip()
        

    print("Avslutar Radio Pi")
   
    
if __name__ == "__main__":
    main()
