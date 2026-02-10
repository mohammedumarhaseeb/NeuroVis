"""
Data schemas for MRI brain tumor analysis system.
Contains only structure definitions, no logic.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MRISequenceType(str, Enum):
    """Standard MRI sequence types for brain tumor imaging"""
    T1 = "T1"
    T1C = "T1c"  # T1 with contrast
    T2 = "T2"
    FLAIR = "FLAIR"


class DicomSeries(BaseModel):
    """Represents a single MRI sequence/series"""
    series_uid: str = Field(..., description="DICOM SeriesInstanceUID")
    series_description: str = Field(..., description="Series description from DICOM header")
    modality: str = Field(..., description="DICOM modality (should be MR)")
    sequence_type: Optional[MRISequenceType] = Field(None, description="Detected sequence type")
    file_paths: List[str] = Field(default_factory=list, description="Paths to DICOM files in this series")
    num_slices: int = Field(0, description="Number of slices in this series")
    
    class Config:
        use_enum_values = True


class DicomStudy(BaseModel):
    """Represents a complete MRI study"""
    study_uid: str = Field(..., description="DICOM StudyInstanceUID")
    patient_id: str = Field("ANONYMOUS", description="Patient identifier")
    study_date: Optional[str] = Field(None, description="Study date")
    study_description: Optional[str] = Field(None, description="Study description")
    series: List[DicomSeries] = Field(default_factory=list, description="List of series in this study")
    
    def get_series_by_type(self, seq_type: MRISequenceType) -> Optional[DicomSeries]:
        """Find a series by sequence type"""
        for series in self.series:
            # Handle both enum and string comparison (use_enum_values converts to string)
            if series.sequence_type == seq_type or series.sequence_type == seq_type.value:
                return series
        return None


class ValidationResult(BaseModel):
    """Result of medical validation"""
    is_valid: bool = Field(..., description="Whether the study passed validation")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    preview_image: Optional[str] = Field(None, description="Base64 encoded MRI preview image")
    required_sequences: Dict[str, bool] = Field(
        default_factory=dict, 
        description="Status of required sequences {sequence_name: present}"
    )


class TumorSegmentation(BaseModel):
    """Tumor segmentation result"""
    whole_tumor_volume_ml: float = Field(..., description="Whole tumor volume in mL")
    enhancing_tumor_volume_ml: float = Field(..., description="Enhancing tumor volume in mL")
    necrotic_core_volume_ml: float = Field(..., description="Necrotic core volume in mL")
    segmentation_map: Optional[str] = Field(None, description="Base64 encoded segmentation overlay")
    disease_heatmap: Optional[str] = Field(None, description="Base64 encoded disease severity heatmap")
    tumor_density_heatmap: Optional[str] = Field(None, description="Base64 encoded tumor density heatmap (seaborn)")
    tumor_region_grid: Optional[str] = Field(None, description="Base64 encoded tumor region grid analysis")
    intensity_distribution: Optional[str] = Field(None, description="Base64 encoded intensity distribution plot")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Segmentation confidence")


class GenotypeIPrediction(BaseModel):
    """Genotype prediction result"""
    idh_mutation_probability: float = Field(..., ge=0.0, le=1.0, description="IDH mutation probability")
    idh_wildtype_probability: float = Field(..., ge=0.0, le=1.0, description="IDH wildtype probability")
    mgmt_methylation_probability: float = Field(..., ge=0.0, le=1.0, description="MGMT promoter methylation probability")
    egfr_amplification_probability: float = Field(..., ge=0.0, le=1.0, description="EGFR amplification probability")
    prediction_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall prediction confidence")


class ExplainabilityData(BaseModel):
    """Explainability and attention maps"""
    attention_maps: Dict[str, str] = Field(
        default_factory=dict, 
        description="Base64 encoded attention/Grad-CAM maps per sequence"
    )
    important_features: List[str] = Field(
        default_factory=list, 
        description="List of important features for the prediction"
    )
    explanation_text: str = Field("", description="Human-readable explanation")


class ClinicalFlags(BaseModel):
    """Clinical risk and urgency flags"""
    high_risk: bool = Field(False, description="High-risk tumor indicators")
    requires_urgent_review: bool = Field(False, description="Requires urgent clinical review")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    urgency_reason: Optional[str] = Field(None, description="Reason for urgency flag")


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    study_id: str = Field(..., description="Unique study identifier")
    timestamp: str = Field(..., description="Analysis timestamp")
    validation: ValidationResult = Field(..., description="Validation result")
    segmentation: Optional[TumorSegmentation] = Field(None, description="Segmentation result")
    genotype_prediction: Optional[GenotypeIPrediction] = Field(None, description="Genotype prediction")
    explainability: Optional[ExplainabilityData] = Field(None, description="Explainability data")
    clinical_flags: Optional[ClinicalFlags] = Field(None, description="Clinical flags")
    processing_time_seconds: float = Field(..., description="Total processing time")


class UploadResponse(BaseModel):
    """Response after file upload"""
    study_id: str = Field(..., description="Unique study identifier")
    message: str = Field(..., description="Upload status message")
    files_received: int = Field(..., description="Number of files received")
    preview_image: Optional[str] = Field(None, description="Base64 encoded MRI preview image")


class InferenceRequest(BaseModel):
    """Request to trigger inference"""
    study_id: str = Field(..., description="Study identifier")
    run_segmentation: bool = Field(True, description="Whether to run segmentation")
    run_genotype_prediction: bool = Field(True, description="Whether to run genotype prediction")
    generate_explanations: bool = Field(True, description="Whether to generate explanations")
    bypass_validation: bool = Field(False, description="⚠️ UNSAFE: Bypass medical validation (for testing only)")
