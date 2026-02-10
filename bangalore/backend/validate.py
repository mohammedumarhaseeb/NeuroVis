"""
Medical validation module.
Acts as the medical gatekeeper - validates studies before allowing inference.
This is the ONLY module that determines if a study is medically valid.
"""
import logging
from typing import List

from schemas import DicomStudy, ValidationResult, MRISequenceType

logger = logging.getLogger(__name__)


class MedicalValidator:
    """Validates MRI studies for medical completeness and correctness"""
    
    # Required sequences for brain tumor analysis
    REQUIRED_SEQUENCES = [
        MRISequenceType.T1,
        MRISequenceType.T2,
        MRISequenceType.FLAIR
    ]
    
    # Minimum number of slices per sequence
    MIN_SLICES_PER_SEQUENCE = 1
    
    def __init__(self):
        """Initialize medical validator"""
        logger.info("MedicalValidator initialized")
    
    def validate_modality(self, study: DicomStudy) -> tuple[bool, List[str]]:
        """
        Validate that all series are MRI
        
        Args:
            study: DicomStudy object
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not study.series:
            errors.append("Study contains no series")
            return False, errors
        
        for series in study.series:
            if series.modality != "MR":
                errors.append(
                    f"Series '{series.series_description}' has invalid modality '{series.modality}'. "
                    f"Expected 'MR' for MRI. This system only accepts MRI studies."
                )
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug("Modality validation passed - all series are MRI")
        else:
            logger.warning(f"Modality validation failed: {errors}")
        
        return is_valid, errors
    
    def validate_required_sequences(self, study: DicomStudy) -> tuple[bool, List[str], dict]:
        """
        Validate that all required sequences are present
        
        Args:
            study: DicomStudy object
            
        Returns:
            Tuple of (is_valid, error_messages, sequence_status_dict)
        """
        errors = []
        sequence_status = {}
        
        for required_seq in self.REQUIRED_SEQUENCES:
            series = study.get_series_by_type(required_seq)
            is_present = series is not None
            sequence_status[required_seq.value] = is_present
            
            if not is_present:
                errors.append(
                    f"Missing required sequence: {required_seq.value}. "
                    f"Brain tumor analysis requires T1, T2, and FLAIR sequences."
                )
            else:
                logger.debug(f"Required sequence {required_seq.value} found: {series.series_description}")
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug("Required sequences validation passed")
        else:
            logger.warning(f"Required sequences validation failed: {errors}")
        
        return is_valid, errors, sequence_status
    
    def validate_slice_counts(self, study: DicomStudy) -> tuple[bool, List[str], List[str]]:
        """
        Validate that sequences have sufficient slices
        
        Args:
            study: DicomStudy object
            
        Returns:
            Tuple of (is_valid, error_messages, warning_messages)
        """
        errors = []
        warnings = []
        
        for series in study.series:
            # Skip series without detected sequence type
            if series.sequence_type is None:
                continue
                
            # Handle both enum and string (use_enum_values converts to string)
            seq_type_value = series.sequence_type if isinstance(series.sequence_type, str) else series.sequence_type.value
            
            if series.sequence_type in self.REQUIRED_SEQUENCES or seq_type_value in [s.value for s in self.REQUIRED_SEQUENCES]:
                if series.num_slices < self.MIN_SLICES_PER_SEQUENCE:
                    errors.append(
                        f"Sequence {seq_type_value} has only {series.num_slices} slices. "
                        f"Minimum {self.MIN_SLICES_PER_SEQUENCE} slices required for reliable analysis."
                    )
                elif series.num_slices < 5:
                    warnings.append(
                        f"Sequence {seq_type_value} has only {series.num_slices} slices. "
                        f"More slices (20+) recommended for optimal analysis quality."
                    )
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.debug("Slice count validation passed")
        else:
            logger.warning(f"Slice count validation failed: {errors}")
        
        return is_valid, errors, warnings
    
    def validate_study(self, study: DicomStudy) -> ValidationResult:
        """
        Perform complete medical validation of the study
        
        This is the main gatekeeper function. If this returns is_valid=False,
        NO inference should be performed.
        
        Args:
            study: DicomStudy object
            
        Returns:
            ValidationResult with detailed status
        """
        logger.info(f"Starting medical validation for study {study.study_uid}")
        
        all_errors = []
        all_warnings = []
        sequence_status = {}
        
        # 1. Validate modality
        modality_valid, modality_errors = self.validate_modality(study)
        all_errors.extend(modality_errors)
        
        # 2. Validate required sequences
        sequences_valid, sequence_errors, sequence_status = self.validate_required_sequences(study)
        all_errors.extend(sequence_errors)
        
        # 3. Validate slice counts
        slices_valid, slice_errors, slice_warnings = self.validate_slice_counts(study)
        all_errors.extend(slice_errors)
        all_warnings.extend(slice_warnings)
        
        # Overall validation status
        is_valid = modality_valid and sequences_valid and slices_valid
        
        result = ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            required_sequences=sequence_status
        )
        
        if is_valid:
            logger.info(f"✓ Study {study.study_uid} passed validation")
        else:
            logger.warning(f"✗ Study {study.study_uid} FAILED validation with {len(all_errors)} errors")
        
        return result
    
    def get_validation_summary(self, validation: ValidationResult) -> str:
        """
        Get human-readable validation summary
        
        Args:
            validation: ValidationResult object
            
        Returns:
            Human-readable summary string
        """
        if validation.is_valid:
            summary = "✓ Study validation PASSED. All required sequences present. Ready for AI analysis."
        else:
            summary = f"✗ Study validation FAILED. {len(validation.errors)} errors found:\n"
            for i, error in enumerate(validation.errors, 1):
                summary += f"\n{i}. {error}"
        
        if validation.warnings:
            summary += f"\n\n⚠ {len(validation.warnings)} warnings:"
            for i, warning in enumerate(validation.warnings, 1):
                summary += f"\n{i}. {warning}"
        
        return summary
