from PIL import Image

# Ganti dengan path ke file PNG kamu
file_path = "sizing/3d (136).png"

# Buka gambar
with Image.open(file_path) as img:
    print("Format:", img.format)
    print("Ukuran:", img.size)
    print("Mode warna:", img.mode)
    
    # Metadata tambahan (jika tersedia)
    info = img.info
    print("\nMetadata tambahan:")
    for key, value in info.items():
        print(f"{key}: {value}")
