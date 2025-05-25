import os
import xml.etree.ElementTree as ET
from PIL import Image
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import subprocess

MAX_DIMENSION = 7000

def extract_xmp_from_jpeg(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    start = data.find(b'<x:xmpmeta')
    end = data.find(b'</x:xmpmeta')
    if start != -1 and end != -1:
        xmp_bytes = data[start:end+12]  # len('</x:xmpmeta>') = 12
        return xmp_bytes
    return None

def extract_xmp_metadata(xmp_content):
    if not xmp_content:
        return "", "", []
    try:
        xmp_str = xmp_content.decode("utf-8", errors="ignore")
        root = ET.fromstring(xmp_str)
    except ET.ParseError:
        return "", "", []

    ns = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    desc = root.find(".//rdf:Description", ns)
    if desc is None:
        return "", "", []

    title_elem = desc.find(".//dc:title/rdf:Alt/rdf:li", ns)
    title = title_elem.text if title_elem is not None else ""

    desc_elem = desc.find(".//dc:description/rdf:Alt/rdf:li", ns)
    description = desc_elem.text if desc_elem is not None else ""

    keywords = [li.text for li in desc.findall(".//dc:subject/rdf:Bag/rdf:li", ns)]

    return title, description, keywords

def resize_and_save_jpeg(input_path, output_folder, file_index):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    new_filename = f"{timestamp}_{file_index:03d}.jpg"
    output_path = os.path.join(output_folder, new_filename)

    try:
        # Baca metadata XMP (opsional)
        xmp_data = extract_xmp_from_jpeg(input_path)
        title, description, keywords = extract_xmp_metadata(xmp_data)

        # Resize gambar
        with Image.open(input_path) as img:
            width, height = img.size
            if max(width, height) > MAX_DIMENSION:
                scale = MAX_DIMENSION / max(width, height)
                new_size = (int(width * scale), int(height * scale))
                resized_image = img.resize(new_size, Image.LANCZOS)
            else:
                resized_image = img.copy()

            # Simpan hasil resize
            resized_image.save(output_path, format="JPEG", quality=95, optimize=True)

        # Salin semua metadata dari gambar asli
        subprocess.run([
    "exiftool",
    "-overwrite_original",
    f"-TagsFromFile={input_path}",
    "-XMP-dc:title",
    "-XMP-dc:description",
    "-XMP-dc:subject",
    output_path
], check=True)

        # (Opsional) Simpan XMP ke file terpisah
        if xmp_data:
            xmp_sidecar = output_path + ".xmp"
            with open(xmp_sidecar, "wb") as f:
                f.write(xmp_data)

    except Exception as e:
        print(f"Error processing {filename}: {e}")

def process_jpeg_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder)
                   if f.lower().endswith(('.jpg', '.jpeg'))]

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(lambda f, idx: resize_and_save_jpeg(f, output_folder, idx),
                               image_files, range(1, len(image_files) + 1)),
                  total=len(image_files),
                  desc="Processing JPEG Images"))

if __name__ == "__main__":
    input_folder = "sizing"
    output_folder = "sizing_out_jpg"
    process_jpeg_folder(input_folder, output_folder)
