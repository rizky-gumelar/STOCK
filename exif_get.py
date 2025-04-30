from PIL import Image
import xml.etree.ElementTree as ET

def extract_xmp_metadata(xmp_content):
    # Pastikan dalam bentuk string
    if isinstance(xmp_content, bytes):
        xmp_str = xmp_content.decode("utf-8", errors="ignore")
    else:
        xmp_str = str(xmp_content)

    root = ET.fromstring(xmp_str)

    ns = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    desc = root.find(".//rdf:Description", ns)

    title_elem = desc.find(".//dc:title/rdf:Alt/rdf:li", ns)
    title = title_elem.text if title_elem is not None else ""

    desc_elem = desc.find(".//dc:description/rdf:Alt/rdf:li", ns)
    description = desc_elem.text if desc_elem is not None else ""

    keywords = [li.text for li in desc.findall(".//dc:subject/rdf:Bag/rdf:li", ns)]

    return title, description, keywords

# Ambil dan ekstrak metadata dari file PNG
with Image.open("file_baru.png") as img:
    xmp_data = img.info.get("XML:com.adobe.xmp")

    if xmp_data:
        title, description, keywords = extract_xmp_metadata(xmp_data)
        print("Judul:", title)
        print("Deskripsi:", description)
        print("Keywords:", keywords)
    else:
        print("XMP metadata tidak ditemukan.")
