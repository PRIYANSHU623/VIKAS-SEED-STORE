import fitz

def extract_text(pdf_path: str):
    document = fitz.open(pdf_path)
    text = ""
    for page in document:
        text+=page.get_text()
        
    document.close()
    
    return text

def chunk_text(text: str, chunk_size: int= 800, overlap: int =100):
    chunks =[]

    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        chunks.append(text[start:end])
        
        start += chunk_size - overlap
        
        return chunks
        
        