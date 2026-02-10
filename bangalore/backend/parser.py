"""
DICOM parser module.
Reads DICOM headers and groups slices into logical sequences.
Contains NO validation logic.
"""
import os
from typing import List, Dict, Optional
import logging
import pydicom
from collections import defaultdict

from schemas import DicomStudy, DicomSeries, MRISequenceType

logger = logging.getLogger(__name__)


class DicomParser:
    """Parses DICOM files and extracts metadata"""
    
    SEQUENCE_KEYWORDS = {
        MRISequenceType.T1: ['t1', 't1w', 't1_weighted', 't1-weighted'],
        MRISequenceType.T1C: ['t1c', 't1ce', 't1+c', 't1_post', 't1_gad', 'contrast', 'post_contrast'],
        MRISequenceType.T2: ['t2', 't2w', 't2_weighted', 't2-weighted'],
        MRISequenceType.FLAIR: ['flair', 'fl air', 't2_flair'],
    }
    
    def __init__(self):
        """Initialize DICOM parser"""
        logger.info("DicomParser initialized")
    
    def read_dicom_file(self, filepath: str) -> Optional[pydicom.Dataset]:
        """
        Read a single DICOM file
        
        Args:
            filepath: Path to DICOM file
            
        Returns:
            pydicom Dataset or None if read fails
        """
        try:
            dcm = pydicom.dcmread(filepath, force=True)
            return dcm
        except Exception as e:
            logger.warning(f"Failed to read DICOM file {filepath}: {e}")
            return None
    
    def extract_series_metadata(self, dcm: pydicom.Dataset, filepath: str) -> Dict:
        """
        Extract relevant metadata from DICOM dataset
        
        Args:
            dcm: pydicom Dataset
            filepath: Path to DICOM file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'filepath': filepath,
            'series_uid': getattr(dcm, 'SeriesInstanceUID', 'UNKNOWN'),
            'study_uid': getattr(dcm, 'StudyInstanceUID', 'UNKNOWN'),
            'modality': getattr(dcm, 'Modality', 'UNKNOWN'),
            'series_description': getattr(dcm, 'SeriesDescription', '').strip(),
            'patient_id': getattr(dcm, 'PatientID', 'ANONYMOUS'),
            'study_date': getattr(dcm, 'StudyDate', None),
            'study_description': getattr(dcm, 'StudyDescription', '').strip(),
            'instance_number': getattr(dcm, 'InstanceNumber', 0),
        }
        return metadata
    
    def detect_sequence_type(self, series_description: str) -> Optional[MRISequenceType]:
        """
        Detect MRI sequence type from series description
        
        Args:
            series_description: DICOM SeriesDescription field
            
        Returns:
            Detected sequence type or None
        """
        desc_lower = series_description.lower()
        
        # Check each sequence type's keywords
        for seq_type, keywords in self.SEQUENCE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    # Special handling for T1 vs T1C
                    if seq_type == MRISequenceType.T1:
                        # Check if it's actually T1C
                        t1c_keywords = self.SEQUENCE_KEYWORDS[MRISequenceType.T1C]
                        if any(kw in desc_lower for kw in t1c_keywords):
                            logger.debug(f"Series '{series_description}' detected as T1C (not T1)")
                            return MRISequenceType.T1C
                    
                    logger.debug(f"Series '{series_description}' detected as {seq_type.value}")
                    return seq_type
        
        logger.debug(f"Series '{series_description}' - sequence type not detected")
        return None
    
    def group_series(self, file_paths: List[str]) -> Dict[str, List[Dict]]:
        """
        Group DICOM files by SeriesInstanceUID
        
        Args:
            file_paths: List of DICOM file paths
            
        Returns:
            Dictionary mapping SeriesInstanceUID to list of file metadata
        """
        series_groups = defaultdict(list)
        
        for filepath in file_paths:
            dcm = self.read_dicom_file(filepath)
            if dcm is None:
                continue
            
            metadata = self.extract_series_metadata(dcm, filepath)
            series_uid = metadata['series_uid']
            series_groups[series_uid].append(metadata)
        
        logger.info(f"Grouped {len(file_paths)} files into {len(series_groups)} series")
        return series_groups
    
    def build_dicom_series(self, series_metadata_list: List[Dict]) -> DicomSeries:
        """
        Build a DicomSeries object from grouped metadata
        
        Args:
            series_metadata_list: List of metadata dicts for a series
            
        Returns:
            DicomSeries object
        """
        # Use first file for series-level metadata
        first = series_metadata_list[0]
        
        # Sort by instance number
        sorted_files = sorted(series_metadata_list, key=lambda x: x['instance_number'])
        
        series = DicomSeries(
            series_uid=first['series_uid'],
            series_description=first['series_description'],
            modality=first['modality'],
            sequence_type=self.detect_sequence_type(first['series_description']),
            file_paths=[m['filepath'] for m in sorted_files],
            num_slices=len(sorted_files)
        )
        
        return series
    
    def parse_study(self, file_paths: List[str]) -> DicomStudy:
        """
        Parse DICOM files into a structured DicomStudy
        
        Args:
            file_paths: List of DICOM file paths
            
        Returns:
            DicomStudy object
        """
        if not file_paths:
            logger.warning("No DICOM files provided to parse")
            return DicomStudy(
                study_uid="EMPTY",
                series=[]
            )
        
        # Group files by series
        series_groups = self.group_series(file_paths)
        
        # Build series objects
        series_list = []
        study_uid = "UNKNOWN"
        patient_id = "ANONYMOUS"
        study_date = None
        study_description = ""
        
        for series_uid, metadata_list in series_groups.items():
            series = self.build_dicom_series(metadata_list)
            series_list.append(series)
            
            # Extract study-level info from first series
            if study_uid == "UNKNOWN":
                study_uid = metadata_list[0]['study_uid']
                patient_id = metadata_list[0]['patient_id']
                study_date = metadata_list[0]['study_date']
                study_description = metadata_list[0]['study_description']
        
        study = DicomStudy(
            study_uid=study_uid,
            patient_id=patient_id,
            study_date=study_date,
            study_description=study_description,
            series=series_list
        )
        
        logger.info(f"Parsed study {study_uid} with {len(series_list)} series")
        return study
