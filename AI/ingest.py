"""
one time setup script
"""

from rag import create_collection, ingest_file
from pypdf import PdfReader, PdfWriter

writer = PdfWriter()
for filename in ["Advanced_marathoning.pdf"]: # was supposed to be more thorough
    reader = PdfReader(filename)
    for page in reader.pages:
        writer.add_page(page)

with open("texts.pdf", "wb") as f:
    writer.write(f)

# Read merged PDF and extract text
reader = PdfReader("texts.pdf")

text = []
for page in reader.pages:
    page_text = page.extract_text()
    if page_text:  # extract_text() may return None
        text.append(page_text)

full_text = "\n\n".join(text)

create_collection("transcripts")
ingest_file(full_text, "transcripts")
