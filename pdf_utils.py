
import pymupdf


def extract_pdf_text(pdf_bytes):
    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    try:
        pages = []

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")

            if text.strip():
                pages.append(
                    f"[Page {page_number}]\n{text}"
                )

        return "\n\n".join(pages)

    finally:
        document.close()
