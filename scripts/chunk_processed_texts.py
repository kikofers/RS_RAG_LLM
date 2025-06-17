import os
from pathlib import Path

def chunk_text(text, chunk_size=500):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i+chunk_size])

def main():
    # Get the absolute path to the script's parent directory (root)
    root_dir = Path(__file__).resolve().parent.parent
    input_dir = root_dir / 'processed_text'
    english_dir = input_dir / 'english'
    output_dir = root_dir / 'chunks'
    output_dir.mkdir(exist_ok=True)

    # Process default language files
    for file in input_dir.glob('*.txt'):
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        for idx, chunk in enumerate(chunk_text(text)):
            chunk_filename = output_dir / f"{file.stem}_chunk{idx+1}.txt"
            with open(chunk_filename, 'w', encoding='utf-8') as out:
                out.write(chunk)
        print(f"Chunked {file.name}")

    # Process English files
    if english_dir.exists():
        for file in english_dir.glob('*.txt'):
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
            for idx, chunk in enumerate(chunk_text(text)):
                chunk_filename = output_dir / f"english_{file.stem}_chunk{idx+1}.txt"
                with open(chunk_filename, 'w', encoding='utf-8') as out:
                    out.write(chunk)
            print(f"Chunked english/{file.name}")

if __name__ == '__main__':
    main()
