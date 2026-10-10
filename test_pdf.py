
from pdf_utils import extract_pdf_text
from ai_service import generate_plan
import json

# Replace this with the name of your test PDF.
pdf_path = "assignment.pdf"

with open(pdf_path, "rb") as file:
    pdf_bytes = file.read()

brief = extract_pdf_text(pdf_bytes)

if not brief.strip():
    raise ValueError("PDF contains no readable text.")

result = generate_plan(
    brief=brief,
    rubric="",
    comments="",
    members=["Sarah", "John", "Emma", "Alex"]
)

print(json.dumps(result, indent=2))
