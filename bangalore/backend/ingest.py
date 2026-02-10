"""
File ingestion module.
Handles raw file uploads and extraction.
Contains NO medical validation logic.
"""
import os
import zipfile
import shutil
from pathlib import Path
from typing import List, Tuple
import tempfile
import logging

logger = logging.getLogger(__name__)


class FileIngestor:
    """Handles file upload and extraction operations"""
    
    def __init__(self, upload_dir: str = None):
        """
        Initialize file ingestor
        
        Args:
            upload_dir: Directory for temporary file storage
        """
        self.upload_dir = upload_dir or tempfile.mkdtemp(prefix="mri_uploads_")
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"FileIngestor initialized with upload_dir: {self.upload_dir}")
    
    def create_study_directory(self, study_id: str) -> str:
        """
        Create a unique directory for a study
        
        Args:
            study_id: Unique study identifier
            
        Returns:
            Path to study directory
        """
        study_dir = os.path.join(self.upload_dir, study_id)
        os.makedirs(study_dir, exist_ok=True)
        logger.info(f"Created study directory: {study_dir}")
        return study_dir
    
    def save_uploaded_file(self, file_content: bytes, filename: str, study_dir: str) -> str:
        """
        Save an uploaded file to disk
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            study_dir: Directory to save file
            
        Returns:
            Path to saved file
        """
        filepath = os.path.join(study_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)
        logger.debug(f"Saved file: {filepath} ({len(file_content)} bytes)")
        return filepath
    
    def extract_zip(self, zip_path: str, extract_dir: str) -> List[str]:
        """
        Extract ZIP file and return list of extracted files
        
        Args:
            zip_path: Path to ZIP file
            extract_dir: Directory to extract to
            
        Returns:
            List of extracted file paths
        """
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                extracted_files = [
                    os.path.join(extract_dir, name) 
                    for name in zip_ref.namelist() 
                    if not name.endswith('/')
                ]
            logger.info(f"Extracted {len(extracted_files)} files from {zip_path}")
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {zip_path}")
            raise ValueError(f"Invalid ZIP file: {zip_path}")
        
        return extracted_files
    
    def is_dicom_file(self, filepath: str) -> bool:
        """
        Simple heuristic to check if file might be DICOM
        Does NOT validate DICOM structure (that's parser's job)
        
        Args:
            filepath: Path to file
            
        Returns:
            True if file might be DICOM
        """
        # Check file extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.dcm', '.dicom']:
            return True
        
        # Check for DICOM magic bytes (DICM at offset 128)
        try:
            with open(filepath, 'rb') as f:
                f.seek(128)
                magic = f.read(4)
                if magic == b'DICM':
                    return True
        except Exception:
            pass
        
        # If no extension and file is readable, assume it might be DICOM
        # (many DICOM files have no extension)
        if not ext and os.path.isfile(filepath):
            try:
                with open(filepath, 'rb') as f:
                    # Just check if file is readable
                    f.read(1)
                return True
            except Exception:
                pass
        
        return False
    
    def filter_dicom_files(self, file_paths: List[str]) -> List[str]:
        """
        Filter list of files to find potential DICOM files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of potential DICOM file paths
        """
        dicom_files = [
            fp for fp in file_paths 
            if os.path.isfile(fp) and self.is_dicom_file(fp)
        ]
        logger.info(f"Filtered {len(dicom_files)} potential DICOM files from {len(file_paths)} total files")
        return dicom_files
    
    def process_upload(self, files: List[Tuple[str, bytes]], study_id: str) -> List[str]:
        """
        Process uploaded files and return list of DICOM file paths
        
        Args:
            files: List of (filename, file_content) tuples
            study_id: Unique study identifier
            
        Returns:
            List of DICOM file paths ready for parsing
        """
        study_dir = self.create_study_directory(study_id)
        all_files = []
        
        for filename, content in files:
            saved_path = self.save_uploaded_file(content, filename, study_dir)
            all_files.append(saved_path)
            
            # If it's a ZIP file, extract it
            if filename.lower().endswith('.zip'):
                extract_subdir = os.path.join(study_dir, f"extracted_{Path(filename).stem}")
                os.makedirs(extract_subdir, exist_ok=True)
                extracted = self.extract_zip(saved_path, extract_subdir)
                all_files.extend(extracted)
        
        # Filter to find DICOM files
        dicom_files = self.filter_dicom_files(all_files)
        
        logger.info(f"Study {study_id}: Processed {len(files)} uploads, found {len(dicom_files)} DICOM files")
        return dicom_files
    
    def cleanup_study(self, study_id: str):
        """
        Delete all files for a study
        
        Args:
            study_id: Study identifier
        """
        study_dir = os.path.join(self.upload_dir, study_id)
        if os.path.exists(study_dir):
            shutil.rmtree(study_dir)
            logger.info(f"Cleaned up study directory: {study_dir}")
