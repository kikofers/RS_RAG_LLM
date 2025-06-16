from PIL import Image
import pytesseract

images = [
    "https://www.rigassatiksme.lv/files/1_9b38b.png",
    "https://www.rigassatiksme.lv/files/2_89a3f.png",
    "https://www.rigassatiksme.lv/files/informacija_trauksmes_celejam_4ebab.png",
    "https://www.rigassatiksme.lv/files/drizuma_si_bus_pietura_pec_pieprasijuma_0b3ab.png",
    "https://www.rigassatiksme.lv/files/_pv_pec_pieprasijuma_info_(1)_65a1d.png"
]

img = Image.open('image.png')
text = pytesseract.image_to_string(img)
print(text)