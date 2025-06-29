# import os
# from typing import List, Dict, Tuple, Optional

# class DocumentHandler:
#     """
#     Handles document processing from MinIO byte objects.
#     Extracts text content from various file formats based on file extension.
#     """
    
#     def __init__(self, file_objects: List[Tuple[bytes, str]]):
#         """
#         Initialize DocumentHandler with list of (file_data, file_name) tuples.
        
#         Args:
#             file_objects: List of tuples containing (file_data_bytes, file_name)
#         """
#         self.file_objects = file_objects
#         self.valid_files = self.validate_file_format()
#         self.document_texts = []
#         self.document_names = []
#         self.document_metadata = []
#         self.process_documents()
    
#     def validate_file_format(self) -> List[Tuple[bytes, str]]:
#         """
#         Validate file formats based on extensions.
#         Currently supports .txt files, easily extensible for other formats.
        
#         Returns:
#             List of valid (file_data, file_name) tuples
#         """
#         # Supported formats - start with .txt, easily extensible
#         valid_formats = ('.txt',)  # Will expand this as needed
#         valid_files = []
        
#         for file_data, file_name in self.file_objects:
#             if not file_name.lower().endswith(valid_formats):
#                 print(f"Invalid file format: {file_name}")
#                 continue
#             valid_files.append((file_data, file_name))
        
#         print(f"Validated {len(valid_files)} out of {len(self.file_objects)} files")
#         return valid_files
    
#     def get_document_names(self) -> List[str]:
#         """
#         Extract document names (without extensions) from file names.
        
#         Returns:
#             List of document names
#         """
#         names = []
#         for _, file_name in self.valid_files:
#             try:
#                 name, _ = os.path.splitext(os.path.basename(file_name))
#                 names.append(name)
#             except Exception as e:
#                 print(f"Error processing file name '{file_name}': {e}")
#                 names.append("unknown_document")
#         return names
    
#     def extract_text_from_file(self, file_data: bytes, file_name: str) -> str:
#         """
#         Extracts text content from a file based on its extension.
#         Uses simple, direct approaches for each file type.
        
#         Args:
#             file_data: File content as bytes
#             file_name: Name of the file (used for extension detection)
            
#         Returns:
#             Extracted text content as string
#         """
#         file_extension = os.path.splitext(file_name.lower())[1]
        
#         try:
#             if file_extension == '.txt':
#                 return self._extract_txt_file(file_data, file_name)
#             # Add other formats here as needed
#             # elif file_extension == '.pdf':
#             #     return self._extract_pdf_file(file_data, file_name)
#             else:
#                 print(f"Unsupported file format: {file_extension}")
#                 return ""
                
#         except Exception as e:
#             print(f"Error extracting text from {file_name}: {e}")
#             return ""
    
#     def _extract_txt_file(self, file_data: bytes, file_name: str) -> str:
#         """
#         Extract text from .txt files with multiple encoding support.
        
#         Args:
#             file_data: File content as bytes
#             file_name: Name of the file
            
#         Returns:
#             Extracted text content
#         """
#         encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
        
#         for encoding in encodings:
#             try:
#                 text = file_data.decode(encoding)
#                 if text.strip():  
#                     return text
#             except UnicodeDecodeError:
#                 continue
#             except Exception as e:
#                 print(f"Unexpected error with encoding {encoding} for {file_name}: {e}")
#                 continue
        
#         try:
#             return file_data.decode('utf-8', errors='replace')
#         except Exception as e:
#             print(f"Final fallback failed for {file_name}: {e}")
#             return ""
    
#     def process_documents(self):
#         """
#         Process all valid documents to extract text content.
#         Updates document_texts, document_names, and document_metadata.
#         """
#         self.document_texts = []
#         self.document_metadata = []
        
#         for file_data, file_name in self.valid_files:
#             try:
#                 text_content = self.extract_text_from_file(file_data, file_name)
                
#                 if text_content:
#                     self.document_texts.append(text_content)
                    
#                     metadata = {
#                         'file_name': file_name,
#                         'file_size': len(file_data),
#                         'text_length': len(text_content),
#                         'extension': os.path.splitext(file_name.lower())[1]
#                     }
#                     self.document_metadata.append(metadata)
#                 else:
#                     print(f"Warning: No text extracted from {file_name}")
                    
#             except Exception as e:
#                 print(f"Error processing document {file_name}: {e}")
        
#         self.document_names = [
#             os.path.splitext(os.path.basename(meta['file_name']))[0] 
#             for meta in self.document_metadata
#         ]
        
#         print(f"Successfully processed {len(self.document_texts)} documents")
    
#     def get_document_info(self) -> List[Dict]:
#         """
#         Get information about all processed documents.
        
#         Returns:
#             List of dictionaries containing document information
#         """
#         info = []
#         for i, metadata in enumerate(self.document_metadata):
#             doc_info = {
#                 'index': i,
#                 'name': self.document_names[i],
#                 'file_name': metadata['file_name'],
#                 'file_size_bytes': metadata['file_size'],
#                 'text_length_chars': metadata['text_length'],
#                 'extension': metadata['extension']
#             }
#             info.append(doc_info)
#         return info
    
#     def get_text_by_name(self, document_name: str) -> Optional[str]:
#         """
#         Get document text by document name.
        
#         Args:
#             document_name: Name of the document (without extension)
            
#         Returns:
#             Document text if found, None otherwise
#         """
#         try:
#             index = self.document_names.index(document_name)
#             return self.document_texts[index]
#         except ValueError:
#             print(f"Document '{document_name}' not found")
#             return None
    
#     def get_text_by_index(self, index: int) -> Optional[str]:
#         """
#         Get document text by index.
        
#         Args:
#             index: Index of the document
            
#         Returns:
#             Document text if found, None otherwise
#         """
#         if 0 <= index < len(self.document_texts):
#             return self.document_texts[index]
#         else:
#             print(f"Index {index} out of range")
#             return None


def _extract_txt_file(file_data: bytes, file_name: str) -> str:
    """
    Extracts text from .txt files with multiple encoding support.
    This logic is taken directly from your DocumentHandler class.
    """
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
    for encoding in encodings:
        try:
            return file_data.decode(encoding)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Unexpected error with encoding {encoding} for {file_name}: {e}")
            continue
    
    print(f"Warning: Could not decode {file_name} with standard encodings. Falling back to utf-8 with replacement.")
    return file_data.decode('utf-8', errors='replace')

def _extract_unstructured(file_data: bytes, file_name: str) -> str:
    """
    Uses the unstructured library as a powerful general-purpose parser.
    """
    from unstructured.partition.auto import partition
    import io

    try:
        elements = partition(file=io.BytesIO(file_data), file_filename=file_name)
        return "\n\n".join([str(el) for el in elements])
    except Exception as e:
        print(f"Error during unstructured parsing for {file_name}: {e}")
        return _extract_txt_file(file_data, file_name)


def extract_text_from_file(file_data: bytes, file_name: str) -> str:
    """
    Extracts text content from a file's byte data based on its extension.
    This function is called by the Celery task.
    """
    import os
    file_extension = os.path.splitext(file_name.lower())[1]
    
    print(f"Extracting text from '{file_name}' with extension '{file_extension}'")
    
    if file_extension == '.txt':
        return _extract_txt_file(file_data, file_name)
    
    elif file_extension in ['.pdf', '.docx', '.pptx', '.html']:
        return _extract_unstructured(file_data, file_name)
        
    
    else:
        print(f"Unsupported file format '{file_extension}'. Attempting text extraction as a fallback.")
        return _extract_txt_file(file_data, file_name)