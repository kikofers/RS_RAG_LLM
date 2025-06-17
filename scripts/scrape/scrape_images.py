import os
import requests
from PIL import Image
import pytesseract
from io import BytesIO

images = [
    "https://www.rigassatiksme.lv/files/1_9b38b.png",
    "https://www.rigassatiksme.lv/files/2_89a3f.png",
    "https://www.rigassatiksme.lv/files/informacija_trauksmes_celejam_4ebab.png",
    "https://www.rigassatiksme.lv/files/drizuma_si_bus_pietura_pec_pieprasijuma_0b3ab.png",
    "https://www.rigassatiksme.lv/files/_pv_pec_pieprasijuma_info_(1)_65a1d.png"
]

def get_filename_from_url(url, ext):
    name = url.split('/')[-1]
    if not name.lower().endswith(ext):
        name += ext
    return name

# Save images and extracted text to the 'text' directory (like html scraper)
text_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'text')
os.makedirs(text_dir, exist_ok=True)

for url in images:
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img_filename = get_filename_from_url(url, '.png')
        img_path = os.path.join(text_dir, img_filename)
        img.save(img_path)
        text = pytesseract.image_to_string(img)
        txt_filename = img_filename.rsplit('.', 1)[0] + '.txt'
        txt_path = os.path.join(text_dir, txt_filename)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Saved: {txt_path}')
    except Exception as e:
        print(f'Failed to process {url}: {e}')