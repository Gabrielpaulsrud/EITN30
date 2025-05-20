import socket
import subprocess
import signal

LISTEN_IP = "11.11.11.1"
LISTEN_PORT = 5002
TARGET_PORT = 12346

def stream_to_udp(stream_url, target_ip, port, bitrate="190k"):
    print(f"Startar ffmpeg: {stream_url} på länk : udp://{target_ip}:{port}")
    return subprocess.Popen([
        "ffmpeg", "-re", "-i", stream_url,
        "-acodec", "libmp3lame", "-ab", bitrate,
        # ,"-pkt_size" , 512   # Libmp3lame är mest använda mp3-kodaren.
        "-f", "mp3", f"udp://{target_ip}:{port}"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print(f"Startar radioströmningsserver på {LISTEN_IP}:{LISTEN_PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Undvik , OSError: [Errno 98] Address already in use
        s.bind((LISTEN_IP, LISTEN_PORT)) # Kopplar ihop en ip address med en port
        while True:
            data, addr = s.recvfrom(1024) # Returnerar en tuple med datan och vilken address som skickade informationen.
            stream_url = data.decode().strip()
            client_ip = addr[0]
            print(f"Fick kanal-URL från {client_ip}")
            ffmpeg_proc = stream_to_udp(stream_url, client_ip, TARGET_PORT)
            try:
                ffmpeg_proc.wait()
            except KeyboardInterrupt:
                print("Stoppar ffmpeg...")
                ffmpeg_proc.send_signal(signal.SIGINT)
                ffmpeg_proc.wait()
                break

if __name__ == "__main__":
    main()
