from multiprocessing import Pool
from PIL import Image
import numpy as np

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


def process_image(image_path, n_processes=4):
    image = Image.open(image_path)
    fragments = split_image(image, n_processes)

    with Pool(n_processes) as pool:
        processed = pool.map(sobel_filter, fragments)

    result = merge_image(processed)
    result.save("processed_parallel.png")
    print("Zapisano wynik: processed_parallel.png")

if __name__ == "__main__":
    process_image(r"C:\Users\piotr\Downloads\image cyberpunk city.jpg", n_processes=4)
