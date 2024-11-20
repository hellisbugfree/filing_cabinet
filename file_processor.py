import os
import json
from PIL import Image
import pytesseract
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import magic


def process_file(file_path):
    """
    Process a file to extract metadata and OCR content, saving results to a JSON file.
    
    Args:
        file_path (str): Path to the file to process
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist")
        return False
    
    # Get MIME type
    mime_type = magic.Magic(mime=True).from_file(file_path)
    
    # Initialize metadata dictionary
    metadata = {
        "file_name": os.path.basename(file_path),
        "file_size": os.path.getsize(file_path),
        "mime_type": mime_type,
        "ocr_text": "",
        "metadata": {}
    }
    
    # Process based on file type
    if mime_type.startswith('image/'):
        try:
            # Process image
            image = Image.open(file_path)
            
            # Extract image metadata
            metadata["metadata"].update({
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
            })
            
            # Perform OCR
            metadata["ocr_text"] = pytesseract.image_to_string(image)
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return False
            
    elif mime_type == 'application/pdf':
        try:
            # Process PDF
            pdf = PdfReader(file_path)
            
            # Extract PDF metadata
            metadata["metadata"].update(pdf.metadata if pdf.metadata else {})
            
            # Convert PDF to images and perform OCR
            ocr_text = []
            pdf_images = convert_from_path(file_path)
            
            for page_num, image in enumerate(pdf_images):
                text = pytesseract.image_to_string(image)
                ocr_text.append(f"Page {page_num + 1}: {text}")
            
            metadata["ocr_text"] = "\n".join(ocr_text)
            
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return False
    else:
        print(f"Unsupported file type: {mime_type}")
        return False
    
    # Save metadata to JSON file
    output_path = f"{file_path}.filing_meta_data"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        print(f"Metadata saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving metadata: {str(e)}")
        return False
