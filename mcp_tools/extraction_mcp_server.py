"""
MCP Server for Invoice Extraction Tools
"""
from fastmcp import FastMCP
import pdfplumber
from docx import Document
from PIL import Image
import pytesseract
from pathlib import Path
import os

# Initialize FastMCP server
mcp = FastMCP("Invoice Extractor Tools")

def resolve_path(file_path: str) -> Path:
    """Resolve file path to absolute path.
    
    Args:
        file_path: Relative or absolute file path
        
    Returns:
        Absolute Path object
    """
    try:
        path = Path(file_path)
        
        print(f"[MCP] Resolving path: {file_path}")
        
        # If path is already absolute and exists, return it
        if path.is_absolute() and path.exists():
            print(f"[MCP] Path is absolute and exists: {path}")
            return path
        
        # Try relative to current working directory
        if path.exists():
            resolved = path.resolve()
            print(f"[MCP] Path exists relative to CWD: {resolved}")
            return resolved
        
        # Try relative to project root (parent of mcp_tools)
        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        print(f"[MCP] Trying project root path: {full_path}")
        if full_path.exists():
            print(f"[MCP] Found at project root: {full_path}")
            return full_path
        
        # If still not found, try as-is (will raise error later if doesn't exist)
        resolved = path.resolve()
        print(f"[MCP] Path not found, returning resolved: {resolved}")
        return resolved
    except Exception as e:
        print(f"[MCP ERROR] Error resolving path: {e}")
        import traceback
        traceback.print_exc()
        return Path(file_path).resolve()

@mcp.tool()
def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF file.
    
    Args:
        file_path: Path to the PDF file (relative or absolute)
        
    Returns:
        Extracted text content from all pages
    """
    try:
        resolved_path = resolve_path(file_path)
        
        print(f"[MCP] Resolved path: {resolved_path}")
        
        if not resolved_path.exists():
            error_msg = f"PDF file not found: {file_path} (resolved to: {resolved_path})"
            print(f"[MCP ERROR] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        print(f"[MCP] Opening PDF: {resolved_path}")
        with pdfplumber.open(str(resolved_path)) as pdf:
            pages_text = []
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
                    print(f"[MCP] Extracted {len(page_text)} chars from page {i+1}")
            
            text = "\n\n".join(pages_text)
            print(f"[MCP] Total extracted: {len(text)} characters")
            return text
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Error extracting PDF: {str(e)}"
        print(f"[MCP ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

@mcp.tool()
def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX file.
    
    Args:
        file_path: Path to the DOCX file (relative or absolute)
        
    Returns:
        Extracted text content from document
    """
    try:
        resolved_path = resolve_path(file_path)
        
        print(f"[MCP] Resolved path: {resolved_path}")
        
        if not resolved_path.exists():
            error_msg = f"DOCX file not found: {file_path} (resolved to: {resolved_path})"
            print(f"[MCP ERROR] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        print(f"[MCP] Opening DOCX: {resolved_path}")
        doc = Document(str(resolved_path))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        print(f"[MCP] Extracted {len(text)} characters")
        return text
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Error extracting DOCX: {str(e)}"
        print(f"[MCP ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

@mcp.tool()
def extract_image_text_ocr(file_path: str) -> str:
    """Extract text from image using OCR (Tesseract).
    
    Args:
        file_path: Path to the image file (PNG, JPG, JPEG) - relative or absolute
        
    Returns:
        Extracted text content using OCR
    """
    try:
        resolved_path = resolve_path(file_path)
        
        print(f"[MCP] Resolved path: {resolved_path}")
        
        if not resolved_path.exists():
            error_msg = f"Image file not found: {file_path} (resolved to: {resolved_path})"
            print(f"[MCP ERROR] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        print(f"[MCP] Opening image: {resolved_path}")
        image = Image.open(str(resolved_path))
        print(f"[MCP] Running OCR...")
        text = pytesseract.image_to_string(image)
        print(f"[MCP] Extracted {len(text)} characters")
        return text
    except FileNotFoundError:
        raise
    except Exception as e:
        error_msg = f"Error extracting image text: {str(e)}"
        print(f"[MCP ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(error_msg) from e

@mcp.tool()
def get_file_info(file_path: str) -> dict:
    """Get information about a file.
    
    Args:
        file_path: Path to the file (relative or absolute)
        
    Returns:
        Dictionary with file information (name, extension, size)
    """
    resolved_path = resolve_path(file_path)
    return {
        "name": resolved_path.name,
        "extension": resolved_path.suffix,
        "size_bytes": resolved_path.stat().st_size if resolved_path.exists() else 0,
        "exists": resolved_path.exists(),
        "absolute_path": str(resolved_path)
    }

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()