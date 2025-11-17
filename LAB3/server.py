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

def split_image(image, n_parts):
    width, height = image.size
    step = height // n_parts
    return [image.crop((0, i * step, width, (i + 1) * step if i < n_parts - 1 else height))
            for i in range(n_parts)]

def merge_image(fragments):
    widths, heights = zip(*(f.size for f in fragments))
    total_height = sum(heights)
    result = Image.new("L", (widths[0], total_height))
    y_offset = 0
    for frag in fragments:
        result.paste(frag, (0, y_offset))
        y_offset += frag.size[1]
    return result

def server_main(image_path, n_clients):
    image = Image.open(image_path)
    fragments = split_image(image, n_clients)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 2040))
    server_socket.listen(n_clients)
    print("Serwer nasłuchuje...")

    processed_fragments = []
    for i in range(n_clients):
        client_socket, addr = server_socket.accept()
        print(f"Połączono z klientem {i+1}: {addr}")
        send_all(client_socket, fragments[i])
        processed = receive_all(client_socket)
        processed_fragments.append(processed)
        client_socket.close()

    result = merge_image(processed_fragments)
    result.save("processed_distributed.png")
    print("Zapisano wynik: processed_distributed.png")

if __name__ == "__main__":
    server_main(r"C:\Users\piotr\Downloads\schematMiS5.png", n_clients=2)
