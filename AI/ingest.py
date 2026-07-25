"""
one time setup script
"""

from rag import create_collection, ingest_file
from pypdf import PdfReader, PdfWriter

writer = PdfWriter()
for filename in ["faster_road_racing.pdf", "Training_Essentials_for_Ultrarunning.pdf", "Advanced_marathoning.pdf"]:
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
