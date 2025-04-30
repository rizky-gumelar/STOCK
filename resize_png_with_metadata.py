import os
from PIL import Image, PngImagePlugin
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

TARGET_FILESIZE_MB = 35  # Target ukuran file dalam MB (optional, bisa diabaikan untuk PNG)
MAX_DIMENSION = 5500     # Maksimal panjang/lebar pixel

def resize_png_with_metadata(input_path, output_folder):
    filename = os.path.basename(input_path)
    output_path = os.path.join(output_folder, filename)

    try:
        # Buka gambar PNG asli
        original_image = Image.open(input_path)

        # Simpan semua info metadata
        metadata = original_image.info

        # Resize gambar jika perlu
        width, height = original_image.size
        if max(width, height) > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(width, height)
            new_size = (int(width * scale), int(height * scale))
            resized_image = original_image.resize(new_size, Image.LANCZOS)
        else:
            resized_image = original_image.copy()

        # Siapkan metadata baru, hanya ambil title dan keywords
        pnginfo = PngImagePlugin.PngInfo()

        # Periksa apakah metadata ada dan ambil title dan keywords
        if 'Title' in metadata:
            pnginfo.add_text('Title', metadata['Title'])
        if 'Keywords' in metadata:
            pnginfo.add_text('Keywords', metadata['Keywords'])

        # Save gambar hasil resize dengan metadata
        resized_image.save(output_path, format="PNG", pnginfo=pnginfo, optimize=True)

    except Exception as e:
        print(f"Error processing {filename}: {e}")

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder)
                   if f.lower().endswith('.png')]

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(lambda f: resize_png_with_metadata(f, output_folder), image_files),
                  total=len(image_files),
                  desc="Processing PNG Images"))

if __name__ == "__main__":
    input_folder = "sizing"
    output_folder = "sizing_out"

    process_folder(input_folder, output_folder)
