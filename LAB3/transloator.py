import socket
import pickle
import io
from PIL import Image

def receive_pickle(sock):
    length = int.from_bytes(sock.recv(4), 'big')
    data = b''
    while len(data) < length:
        packet = sock.recv(4096)
        if not packet:
            break
        data += packet
    return pickle.loads(data)
def send_png(sock, image):
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    data = buf.getvalue()
    sock.sendall(len(data).to_bytes(4, 'big'))
    sock.sendall(data)

def translator_main(server_ip='192.168.122.224', server_port=2040, translator_port=3050):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((server_ip, server_port))
    print(f"Połączono z serwerem {server_ip}:{server_port}")

    client_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_listener.bind(('0.0.0.0', translator_port))
    client_listener.listen(1)
    print(f"Translator nasłuchuje klienta C# na porcie {translator_port}...")

    client_socket, client_addr = client_listener.accept()
    print(f"Połączono z klientem C#: {client_addr}")


    fragment = receive_pickle(server_socket)
    print("Odebrano fragment z serwera")


    send_png(client_socket, fragment)
    print("Wysłano obraz PNG do klienta C#")


    length = int.from_bytes(client_socket.recv(4), 'big')
    data = b''
    while len(data) < length:
        packet = client_socket.recv(4096)
        if not packet:
            break
        data += packet
    processed_img = Image.open(io.BytesIO(data))
    print("Odebrano przetworzony obraz z klienta C#")


    data_pickle = pickle.dumps(processed_img)
    server_socket.sendall(len(data_pickle).to_bytes(4, 'big'))
    server_socket.sendall(data_pickle)
    print("Wysłano przetworzony obraz do serwera")

    client_socket.close()
    server_socket.close()
    client_listener.close()
    print("Zakończono działanie translatera")

if __name__ == "__main__":
    translator_main()
