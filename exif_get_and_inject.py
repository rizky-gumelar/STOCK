# from PIL import Image
import xml.etree.ElementTree as ET
from PIL import Image, PngImagePlugin

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
with Image.open("sizing/3d (136).png") as img:
    xmp_data = img.info.get("XML:com.adobe.xmp")

    if xmp_data:
        title, description, keywords = extract_xmp_metadata(xmp_data)
        # print("Judul:", title)
        # print("Deskripsi:", description)
        # print("Keywords:", keywords)
    else:
        print("XMP metadata tidak ditemukan.")

# Buat struktur XMP metadata baru
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

# XMP string hasil generate
xmp_string = create_xmp_packet(title, description, keywords)

# Buka gambar asli
original_image = Image.open("sizing/3d (136).png")
new_image = original_image.copy()

# Tambahkan metadata XMP ke file PNG baru
meta = PngImagePlugin.PngInfo()
meta.add_itxt("XML:com.adobe.xmp", xmp_string, lang="en", tkey="x-default")

# Simpan gambar baru
new_image.save("file_baru.png", pnginfo=meta)

print("File baru berhasil disimpan dengan metadata yang disederhanakan.")