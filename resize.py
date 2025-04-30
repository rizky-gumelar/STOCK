import os
from PIL import Image
import piexif
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

TARGET_FILESIZE_MB = 35  # Target ukuran file dalam MB
MAX_DIMENSION = 5000     # Maksimal panjang/lebar pixel

def resize_image_to_target(input_path, output_folder):
    filename = os.path.basename(input_path)
    output_path = os.path.join(output_folder, filename)

    try:
        image = Image.open(input_path)
        exif_data = image.info.get('exif')

        # Resize jika terlalu besar
        width, height = image.size
        if max(width, height) > MAX_DIMENSION:
            scale = MAX_DIMENSION / max(width, height)
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.LANCZOS)

        temp_quality = 95
        image.save(output_path, exif=exif_data, quality=temp_quality, optimize=True)

        filesize_mb = os.path.getsize(output_path) / (1024 * 1024)

        # Turunkan kualitas jika ukuran lebih dari target
        while filesize_mb > TARGET_FILESIZE_MB and temp_quality > 10:
            temp_quality -= 2
            image.save(output_path, exif=exif_data, quality=temp_quality, optimize=True)
            filesize_mb = os.path.getsize(output_path) / (1024 * 1024)

    except Exception as e:
        print(f"Error processing {filename}: {e}")

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder)
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(lambda f: resize_image_to_target(f, output_folder), image_files),
                  total=len(image_files),
                  desc="Processing Images"))

if __name__ == "__main__":
    input_folder = "sizing"   # Ganti sesuai folder kamu
    output_folder = "sizing_out"

    process_folder(input_folder, output_folder)
