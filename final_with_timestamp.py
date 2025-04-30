import os
import xml.etree.ElementTree as ET
from PIL import Image, PngImagePlugin
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

MAX_DIMENSION = 5500  # Maksimal panjang/lebar pixel

def extract_xmp_metadata(xmp_content):
    if isinstance(xmp_content, bytes):
        xmp_str = xmp_content.decode("utf-8", errors="ignore")
    else:
        xmp_str = str(xmp_content)

    try:
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

def resize_and_save_with_metadata(input_path, output_folder, file_index):
    # Ambil tanggal saat ini untuk nama file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Format nama file baru: YYYYMMDD_HHMMSS_urutan.png
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    new_filename = f"{timestamp}_{file_index:03d}{ext}"  # Menambahkan urutan dengan 3 digit (misal: 001, 002, dst)
    output_path = os.path.join(output_folder, new_filename)

    try:
        with Image.open(input_path) as original_image:
            metadata = original_image.info
            xmp_data = metadata.get("XML:com.adobe.xmp")
            title, description, keywords = extract_xmp_metadata(xmp_data) if xmp_data else ("", "", [])

            # Resize jika perlu
            width, height = original_image.size
            if max(width, height) > MAX_DIMENSION:
                scale = MAX_DIMENSION / max(width, height)
                new_size = (int(width * scale), int(height * scale))
                resized_image = original_image.resize(new_size, Image.LANCZOS)
            else:
                resized_image = original_image.copy()

            # Buat XMP baru
            xmp_string = create_xmp_packet(title, description, keywords)

            # Simpan ke file baru dengan metadata XMP
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_itxt("XML:com.adobe.xmp", xmp_string, lang="en", tkey="x-default")

            resized_image.save(output_path, format="PNG", pnginfo=pnginfo, optimize=True)

    except Exception as e:
        print(f"Error processing {filename}: {e}")

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder)
                   if f.lower().endswith('.png')]

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(lambda f, idx: resize_and_save_with_metadata(f, output_folder, idx),
                               image_files, range(1, len(image_files) + 1)),
                  total=len(image_files),
                  desc="Processing PNG Images"))

if __name__ == "__main__":
    input_folder = "sizing"
    output_folder = "sizing_out"
    process_folder(input_folder, output_folder)
