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

def create_xmp_packet(title, description, keywords):
    keyword_tags = "\n".join(f"<rdf:li>{kw}</rdf:li>" for kw in keywords)
    return f"""<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/' x:xmptk='Python'>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
  <rdf:Description rdf:about=''
    xmlns:dc='http://purl.org/dc/elements/1.1/'>
    <dc:title><rdf:Alt><rdf:li xml:lang='x-default'>{title}</rdf:li></rdf:Alt></dc:title>
    <dc:description><rdf:Alt><rdf:li xml:lang='x-default'>{description}</rdf:li></rdf:Alt></dc:description>
    <dc:subject><rdf:Bag>{keyword_tags}</rdf:Bag></dc:subject>
  </rdf:Description>
</rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""


def resize_and_save_jpeg(input_path, output_folder, file_index):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    new_filename = f"{timestamp}_{file_index:03d}.jpg"
    output_path = os.path.join(output_folder, new_filename)

    try:
        # 1. Ambil dan ubah XMP metadata
        xmp_data = extract_xmp_from_jpeg(input_path)
        title, description, keywords = extract_xmp_metadata(xmp_data)

        # 👉 Misal: hapus kata "Rahasia" dari title
        banned_words = ["Rahasia."]
        for word in banned_words:
            title = title.replace(word, "")
            description = description.replace(word, "")

        # Buat XMP baru hasil edit
        new_xmp = create_xmp_packet(title.strip(), description, keywords)
        xmp_file = os.path.join(output_folder, f"{new_filename}.xmp")
        with open(xmp_file, "w", encoding="utf-8") as f:
            f.write(new_xmp)

        # 2. Resize dan simpan JPEG baru
        with Image.open(input_path) as img:
            width, height = img.size
            if max(width, height) > MAX_DIMENSION:
                scale = MAX_DIMENSION / max(width, height)
                new_size = (int(width * scale), int(height * scale))
                resized_image = img.resize(new_size, Image.LANCZOS)
            else:
                resized_image = img.copy()
            resized_image.save(output_path, "JPEG", quality=95, optimize=True)

        # 3. Inject XMP hasil edit ke file JPEG dengan exiftool
        subprocess.run([
            "exiftool",
            "-overwrite_original",
            f"-XMP<={xmp_file}",
            output_path
        ], check=True)

        # (Opsional) Hapus file sidecar XMP jika tidak dibutuhkan
        os.remove(xmp_file)

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
