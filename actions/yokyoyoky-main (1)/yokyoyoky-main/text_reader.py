# actions/text_reader.py
import os
from pathlib import Path
from typing import Optional

class TextReader:
    def __init__(self):
        pass

    def read_document(self, file_path: str) -> str:
        """
        Belge okuma fonksiyonu. PDF, DOCX, TXT ve diğer metin dosyalarını okur.
        """
        if not file_path:
            return "Dosya yolu belirtilmedi, efendim."
        
        path = Path(file_path.strip('"\' '))
        
        if not path.exists():
            return f"Dosya bulunamadı: '{file_path}'"
        
        if not path.is_file():
            return f"Belirtilen yol bir dosya değil: '{file_path}'"
        
        # Dosya boyutu kontrolü (max 20MB)
        file_size = path.stat().st_size
        max_size = 20 * 1024 * 1024  # 20 MB
        if file_size > max_size:
            return f"Dosya çok büyük ({file_size // (1024*1024)} MB). Maksimum 20 MB destekleniyor."
        
        ext = path.suffix.lower()
        content = ""
        
        try:
            # --- PDF ---
            if ext == '.pdf':
                try:
                    import PyPDF2
                except ImportError:
                    return "PDF okuma için 'PyPDF2' kütüphanesi gerekli. 'pip install PyPDF2' ile kurabilirsiniz."
                try:
                    with open(path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        num_pages = len(reader.pages)
                        if num_pages > 50:
                            return f"PDF çok fazla sayfa içeriyor ({num_pages}). En fazla 50 sayfa okunabilir."
                        for page_num, page in enumerate(reader.pages):
                            text = page.extract_text()
                            if text:
                                content += f"\n--- Sayfa {page_num+1} ---\n{text}"
                except Exception as e:
                    return f"PDF okuma hatası: {str(e)}"
            
            # --- DOCX / DOC ---
            elif ext in ['.docx', '.doc']:
                try:
                    import docx
                except ImportError:
                    return "Word dosyası okuma için 'python-docx' kütüphanesi gerekli. 'pip install python-docx' ile kurabilirsiniz."
                try:
                    doc = docx.Document(path)
                    content = "\n".join([para.text for para in doc.paragraphs])
                except Exception as e:
                    return f"Word belgesi okuma hatası: {str(e)}"
            
            # --- Düz metin dosyaları (TXT, PY, JSON, CSV, MD, HTML, vs.) ---
            else:
                # Encoding algılamayı dene (chardet yoksa utf-8)
                encoding = 'utf-8'
                try:
                    import chardet
                    with open(path, 'rb') as f:
                        raw = f.read(1024)
                        result = chardet.detect(raw)
                        if result['encoding']:
                            encoding = result['encoding']
                except ImportError:
                    pass
                
                with open(path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
            
            # İçerik kontrolü
            if not content or not content.strip():
                return f"Dosya boş veya okunamıyor: {path.name}"
            
            # Uzun dosyaları kırp (satır bazında 500 satır)
            lines = content.splitlines()
            max_lines = 500
            if len(lines) > max_lines:
                truncated = lines[:max_lines]
                content = "\n".join(truncated)
                content += f"\n\n... [Dosya çok uzun, ilk {max_lines} satır gösteriliyor. Toplam {len(lines)} satır]"
            
            # Dosya bilgilerini ekle
            file_info = f"📄 {path.name} ({file_size // 1024} KB)\n{'='*50}\n"
            return file_info + content
        
        except Exception as e:
            return f"Dosya okunurken hata oluştu: {str(e)}"