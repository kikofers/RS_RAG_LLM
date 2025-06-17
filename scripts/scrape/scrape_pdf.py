from pypdf import PdfReader
import re
from scrape_html import normalize_white_spaces

pdfs = [
    "https://www.rigassatiksme.lv/files/pasazieru_iekapsanas_un_izkapsanas_kartibas_noteikumi_konsolideti_ar_groz_1.pdf",
    "https://www.rigassatiksme.lv/files/noteikumi_abonementa_bilesu_izmantosanas_kartiba_konsolidets_ar_groz_5.pdf",
    "https://www.rigassatiksme.lv/files/brauksanas_maksas_atvieglojumu_pieskirsanas_kartiba_ar_groz_12.pdf",
    "https://www.rigassatiksme.lv/files/noteikumi_par_pasazieru_parvadajumu_kontroli_konsolideti_ar_groz_10.pdf",
    "https://www.rigassatiksme.lv/files/1_velosipedu_parvadasanas_kartiba_sabiedriska_transportlidzekla_salona.pdf",
    "https://www.rigassatiksme.lv/files/tikas_komisijas_reglaments_konsolidets_ar_groz_1_03_10_2024.pdf"
]

# Analyzes (heuristically) line breaks and merges lines if necessary.
def merge_lines(text):
    # If a line ends with a lower case letter followed by a hyphen,
    # we *assume* this is a hyhenation of a word.
    text = re.sub(r"(?<=[a-zāčēģīķļņšūž])[--]\n(?=[a-zāčēģīķļņšūž])", "", text)

    # If a line begins with a lower case letter,
    # we *assume* this is a continuation of a sentence.
    text = re.sub(r"(\n)+(?=[a-zāčēģīķļņšūž])", " ", text) # FIXME: \p{Ll}

    return text


# A more elaborate implementation of the basic text extractor
def pdf_to_txt_2(pdf_file, txt_file):
    text = ""

    with open(pdf_file, "rb") as input_file:
        reader = PdfReader(input_file)

        for page in reader.pages:
            text += page.extract_text() + "\n"

    text = merge_lines(normalize_white_spaces(text))

    with open(txt_file, "w", encoding="utf-8") as output_file:
        output_file.write(text)

    print("Total number of lines in the text:", text.count("\n"))


pdf_to_txt_2("sample_paper.pdf", "sample_paper_2.txt")

# TODO: a potential mini-project - develop an advanced PDF-to-Text extractor