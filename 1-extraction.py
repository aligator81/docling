from docling.document_converter import DocumentConverter
from utils.sitemap import get_sitemap_urls
import os

source = "temp_Sequence_Rules_EN.pdf"  # file path or URL
converter = DocumentConverter()
doc = converter.convert(source).document

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Extract filename from source for output file naming
if source.startswith(("http://", "https://")):
    # For URLs, use domain name as filename
    from urllib.parse import urlparse
    domain = urlparse(source).netloc
    filename = f"output/{domain}_extracted.md"
else:
    # For local files, use the base filename
    base_name = os.path.splitext(os.path.basename(source))[0]
    filename = f"output/{base_name}_extracted.md"

# Save extracted content to file
markdown_content = doc.export_to_markdown()
with open(filename, "w", encoding="utf-8") as f:
    f.write(markdown_content)

print(f"Extraction completed! Content saved to: {filename}")
print(f"Extracted {len(markdown_content)} characters to markdown file.")