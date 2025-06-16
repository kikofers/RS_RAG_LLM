from bs4 import BeautifulSoup
import html
import re
import os
import requests

# List of websites to scrape
# Note: The list of websites is not exhaustive and can be extended with more URLs.
websites = [
    "https://www.rigassatiksme.lv/lv/par-mums/",
    "https://www.rigassatiksme.lv/lv/par-mums/vadiba/",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/menesa-bilete/",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/koda-bilete/",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/laika-bilete/",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/dienas-bilete/",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/brauksanas-apliecinajums-sabiedriskaja-transporta/",
    "https://likumi.lv/ta/id/343388-par-brauksanas-maksas-atvieglojumiem-rigas-valstspilsetas-sabiedriska-transporta-marsrutu-tikla",
    "https://www.rigassatiksme.lv/lv/biletes/bilesu-klasts-un-cenas-1/Person%C4%81m%20ar%20invalidit%C4%81ti/",
    "https://www.rigassatiksme.lv/lv/biletes/koda-bilete/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/personalizetais-e-talons/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/nepersonalizetais-e-talons/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/ridzinieka-karte/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/skolena-e-karte/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/pavadona-karte/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/juridiskas-personas-klienta-karte/",
    "https://www.rigassatiksme.lv/lv/biletes/e-talonu-veidi/dzeltenais-e-talons/",
    "https://www.rigassatiksme.lv/lv/par-mums/pietura-pec-pieprasijuma/"
]

# Removes specific HTML elements from a webpage to get rid of needless content.
# For instance: header and footer blocks, menus, etc.
# Needs to be adapted for each website to get the best results.
def remove_html_elements(text):
    soup = BeautifulSoup(text, "html.parser")

    # Filtering by specific HTML elements
    for element in soup.find_all(["header", "footer", "button"]):
        element.decompose() # Removes an element from the tree

    # Filtering by HTML elements having specific attributes
    for element in soup.find_all(["div"], attrs={"class": re.compile(".*([Mm]enu|share|backlink).*")}):
        element.decompose()

    return str(soup)


# (1) Unescapes HTML entities.
# (2) Removes HTML tags while keeping the content.
# For instance: &amp; => &, <p>content</p> => content.
# This function is universal - it can be applied to any webpage from any website.
def convert_to_plaintext(text):
    text = html.unescape(text)                     # 1
    text = BeautifulSoup(text, "html.parser").text # 2
    return text


# Normalizes spaces and line breaks in the plain-text.
def normalize_white_spaces(text):
    text = re.sub("[ ]+", " ", text)
    text = re.sub("[ ]?\n+", "\n", text)
    return text


# Extracts main content for likumi.lv by getting all <p> tags with class TV213 or TV206
def extract_likumi_lv_main_content(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    # Find all <p> tags with class TV213 or TV206 (with or without additional classes)
    paragraphs = soup.find_all('p', class_=lambda c: c and ("TV213" in c or "TV206" in c))
    # Join the text from all found paragraphs
    return '\n'.join(p.get_text(separator=' ', strip=True) for p in paragraphs)


# (1) Removal of needless HTML elements.
# (2) Unescaping HTML entities and removal of HTML tags.
# (3) Normalization of whitespaces in the plain-text.
def html_to_txt(html_file, txt_file, url=None):
    text = ""

    with open(html_file, "r", encoding="utf-8") as input_file:
        text = input_file.read()

    # Special handling for likumi.lv
    if url and "likumi.lv" in url:
        text = extract_likumi_lv_main_content(text)
    else:
        text = remove_html_elements(text)   # 1
        text = convert_to_plaintext(text)   # 2
        text = normalize_white_spaces(text) # 3
        # Remove footer for rigassatiksme.lv
        if url and "rigassatiksme.lv" in url:
            text = remove_footer_rigassatiksme(text)

    with open(txt_file, "w", encoding="utf-8") as output_file:
        output_file.write(text)

def get_filename_from_url(url):
    # Use the full URL, replace special characters to make a valid filename
    name = url.replace('https://', '').replace('http://', '')
    name = name.replace('/', '_').replace('?', '_').replace('&', '_').replace(':', '_')
    return name + '.txt'

def remove_footer_rigassatiksme(text):
    footer_start = text.find("Mēs izmantojam sīkdatnes")
    if footer_start != -1:
        return text[:footer_start].rstrip()
    return text

text_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'text')

for url in websites:
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'

        html_content = response.text
        filename = get_filename_from_url(url)
        html_file = os.path.join(text_dir, f'temp_{filename}.html')
        txt_file = os.path.join(text_dir, filename)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        html_to_txt(html_file, txt_file, url=url)
        os.remove(html_file)
        print(f'Saved: {txt_file}')

    except Exception as e:
        print(f'Failed to process {url}: {e}')