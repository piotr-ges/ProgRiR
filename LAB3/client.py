import socket
import pickle
from PIL import Image
import numpy as np

def send_all(sock, data):
    data = pickle.dumps(data)
    sock.sendall(len(data).to_bytes(4, 'big'))
    sock.sendall(data)

def receive_all(sock):
    length = int.from_bytes(sock.recv(4), 'big')
    data = b''
    while len(data) < length:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)

def sobel_filter(fragment):
    gray = np.array(fragment.convert("L"), dtype=np.float32)
    Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    Ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    Gx = np.zeros_like(gray)
    Gy = np.zeros_like(gray)
    for i in range(1, gray.shape[0] - 1):
        for j in range(1, gray.shape[1] - 1):
            region = gray[i-1:i+2, j-1:j+2]
            Gx[i, j] = np.sum(Kx * region)
            Gy[i, j] = np.sum(Ky * region)
    G = np.sqrt(Gx**2 + Gy**2)
    G = np.clip(G, 0, 255)
    return Image.fromarray(G.astype(np.uint8))

def client_main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("192.168.122.224", 2040))
    fragment = receive_all(client)
    processed = sobel_filter(fragment)
    send_all(client, processed)
    client.close()
    print("Fragment przetworzony i wysłany do serwera")

if __name__ == "__main__":
    client_main()
