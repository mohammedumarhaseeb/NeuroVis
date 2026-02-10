"""
FastAPI main application.
Exposes REST API endpoints for the brain tumor MRI analysis system.
"""
import os
import uuid
import logging
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
import base64
from io import BytesIO
from PIL import Image

from ingest import FileIngestor
from parser import DicomParser
from validate import MedicalValidator
from ai_pipeline import (
    MockAIModel, TumorSegmentationPipeline, GenotypePredictionPipeline,
    ExplainabilityPipeline, ClinicalFlaggingPipeline
)
from schemas import (
    UploadResponse, InferenceRequest, AnalysisResult, 
    DicomStudy, ValidationResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global storage for studies (in production, use Redis/database)
studies_db = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app"""
    logger.info("🚀 Starting Brain Tumor MRI Analysis API")
    logger.info("="*60)
    
    # Initialize components
    app.state.ingestor = FileIngestor()
    app.state.parser = DicomParser()
    app.state.validator = MedicalValidator()
    app.state.ai_model = MockAIModel()
    app.state.segmentation_pipeline = TumorSegmentationPipeline(app.state.ai_model)
    app.state.genotype_pipeline = GenotypePredictionPipeline(app.state.ai_model)
    app.state.explainability_pipeline = ExplainabilityPipeline(app.state.ai_model)
    app.state.clinical_flagging = ClinicalFlaggingPipeline()
    
    logger.info("✓ All components initialized")
    logger.info("="*60)
    
    yield
    
    logger.info("Shutting down API")


# Create FastAPI app
app = FastAPI(
    title="Brain Tumor MRI Analysis API",
    description="Validation-gated AI system for brain tumor MRI analysis with genotype prediction",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Brain Tumor MRI Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "inference": "/api/inference",
            "results": "/api/results/{study_id}",
            "validation": "/api/validation/{study_id}"
        }
    }


@app.post("/api/upload", response_model=UploadResponse)
async def upload_study(files: List[UploadFile] = File(...)):
    """
    Upload MRI study (DICOM files or ZIP)
    
    This endpoint:
    1. Accepts files
    2. Extracts and filters DICOM files
    3. Parses DICOM headers
    4. Validates the study
    5. Stores parsed study for later inference
    
    Returns study_id and validation status.
    """
    logger.info(f"📥 Received upload request with {len(files)} files")
    
    try:
        # Generate unique study ID
        study_id = str(uuid.uuid4())
        
        # Read file contents
        file_data = []
        for file in files:
            content = await file.read()
            file_data.append((file.filename, content))
            logger.debug(f"Read file: {file.filename} ({len(content)} bytes)")
        
        # Ingest files
        dicom_files = app.state.ingestor.process_upload(file_data, study_id)
        
        if not dicom_files:
            raise HTTPException(
                status_code=400,
                detail="No valid DICOM files found in upload. Please upload MRI DICOM files or a ZIP containing DICOM files."
            )
        
        # Parse DICOM study
        study = app.state.parser.parse_study(dicom_files)
        
        # Validate study
        validation = app.state.validator.validate_study(study)
        
        # Store study and validation
        studies_db[study_id] = {
            'study': study,
            'validation': validation,
            'uploaded_at': datetime.now().isoformat(),
            'result': None,
            'preview_image': None # Will be set below
        }
        
        # Extract MRI preview image from first available DICOM file
        preview_image = None
        try:
            for series in study.series:
                if series.file_paths:
                    dcm = pydicom.dcmread(series.file_paths[0], force=True)
                    if hasattr(dcm, 'pixel_array'):
                        raw = dcm.pixel_array.astype(np.float32)
                        if raw.max() > raw.min():
                            raw = (raw - raw.min()) / (raw.max() - raw.min()) * 255
                        from PIL import Image as PILImage
                        from io import BytesIO as BIO
                        img = PILImage.fromarray(raw.astype(np.uint8))
                        img = img.resize((256, 256))
                        buffered = BIO()
                        img.save(buffered, format="PNG")
                        preview_image = base64.b64encode(buffered.getvalue()).decode()
                        logger.info(f"Generated MRI preview from {series.file_paths[0]}")
                        break
        except Exception as e:
            logger.warning(f"Could not generate preview: {e}")
        
        studies_db[study_id]['preview_image'] = preview_image
        validation.preview_image = preview_image
        
        logger.info(f"✓ Study {study_id} uploaded and validated")
        logger.info(f"  Validation status: {'PASSED' if validation.is_valid else 'FAILED'}")
        logger.info(f"  Series found: {len(study.series)}")
        
        return UploadResponse(
            study_id=study_id,
            message="Study uploaded and validated successfully" if validation.is_valid 
                    else "Study uploaded but validation failed",
            files_received=len(dicom_files),
            preview_image=preview_image
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/validation/{study_id}")
async def get_validation(study_id: str):
    """
    Get validation status for a study
    
    Returns detailed validation results including:
    - Whether study is valid for inference
    - Specific errors and warnings
    - Status of required sequences
    """
    if study_id not in studies_db:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    
    study_data = studies_db[study_id]
    validation = study_data['validation']
    study = study_data['study']
    
    # Ensure preview image is attached to the validation object if it exists in study_db
    if 'preview_image' in study_data:
        validation.preview_image = study_data['preview_image']
    
    summary = app.state.validator.get_validation_summary(validation)
    
    return {
        "study_id": study_id,
        "validation": validation,
        "summary": summary,
        "study_info": {
            "study_uid": study.study_uid,
            "num_series": len(study.series),
            "series_descriptions": [s.series_description for s in study.series]
        }
    }


@app.post("/api/inference")
async def run_inference(request: InferenceRequest, background_tasks: BackgroundTasks):
    """
    Trigger AI inference on a validated study
    
    This is the main analysis endpoint. It:
    1. Checks if study exists
    2. **ENFORCES VALIDATION** - blocks inference if study is invalid
    3. Runs segmentation, genotype prediction, and explainability
    4. Generates clinical flags
    5. Returns complete analysis results
    
    CRITICAL: This endpoint respects the medical validation gate.
    """
    logger.info(f"🧠 Inference request for study {request.study_id}")
    
    # Check if study exists
    if request.study_id not in studies_db:
        raise HTTPException(status_code=404, detail=f"Study {request.study_id} not found")
    
    study_data = studies_db[request.study_id]
    study = study_data['study']
    validation = study_data['validation']
    
    # MEDICAL VALIDATION GATE
    if not validation.is_valid and not request.bypass_validation:
        logger.warning(f"⛔ Inference BLOCKED for study {request.study_id} - validation failed")
        error_summary = app.state.validator.get_validation_summary(validation)
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Study validation failed - inference cannot proceed",
                "validation_summary": error_summary,
                "validation_errors": validation.errors,
                "required_sequences": validation.required_sequences
            }
        )
    
    if request.bypass_validation and not validation.is_valid:
        logger.warning(f"⚠️  BYPASSING VALIDATION for study {request.study_id} - FOR TESTING ONLY")
    
    logger.info(f"✓ Validation passed - proceeding with inference")
    
    try:
        start_time = datetime.now()
        
        # Run tumor segmentation
        segmentation = None
        if request.run_segmentation:
            logger.info("Running tumor segmentation...")
            segmentation = app.state.segmentation_pipeline.run(study)
        
        # Run genotype prediction
        genotype = None
        if request.run_genotype_prediction:
            logger.info("Running genotype prediction...")
            genotype = app.state.genotype_pipeline.run(study, None)
        
        # Generate explanations
        explainability = None
        if request.generate_explanations:
            logger.info("Generating explanations...")
            explainability = app.state.explainability_pipeline.run(
                study, segmentation, genotype
            )
        
        # Generate clinical flags
        logger.info("Evaluating clinical flags...")
        clinical_flags = app.state.clinical_flagging.run(segmentation, genotype)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create result
        result = AnalysisResult(
            study_id=request.study_id,
            timestamp=datetime.now().isoformat(),
            validation=validation,
            segmentation=segmentation,
            genotype_prediction=genotype,
            explainability=explainability,
            clinical_flags=clinical_flags,
            processing_time_seconds=processing_time
        )
        
        # Store result
        studies_db[request.study_id]['result'] = result
        
        logger.info(f"✓ Inference complete for study {request.study_id} ({processing_time:.2f}s)")
        logger.info(f"  High risk: {clinical_flags.high_risk}")
        logger.info(f"  Urgent review: {clinical_flags.requires_urgent_review}")
        
        return result
    
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.get("/api/results/{study_id}")
async def get_results(study_id: str):
    """
    Retrieve analysis results for a study
    
    Returns the complete AnalysisResult if inference has been run,
    otherwise returns validation status only.
    """
    if study_id not in studies_db:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    
    study_data = studies_db[study_id]
    
    if study_data['result'] is None:
        return {
            "study_id": study_id,
            "status": "validation_only",
            "validation": study_data['validation'],
            "message": "Inference has not been run yet. Use /api/inference to run analysis."
        }
    
    return study_data['result']


@app.get("/api/preview/{study_id}")
async def preview_study(study_id: str):
    """
    Get DICOM image previews for a study.
    
    Returns base64-encoded PNG images for each series,
    with a representative middle slice and the ability to 
    request specific slices.
    """
    if study_id not in studies_db:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    
    study_data = studies_db[study_id]
    study = study_data['study']
    
    series_previews = []
    
    for series in study.series:
        if not series.file_paths:
            continue
        
        slice_images = []
        for filepath in series.file_paths:
            try:
                dcm = app.state.parser.read_dicom_file(filepath)
                if dcm is None or not hasattr(dcm, 'pixel_array'):
                    continue
                
                # Convert pixel data to image
                pixel_array = dcm.pixel_array.astype(np.float32)
                if pixel_array.max() > pixel_array.min():
                    pixel_array = (pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255
                pixel_array = pixel_array.astype(np.uint8)
                
                # Convert to PNG base64
                img = Image.fromarray(pixel_array)
                img = img.resize((256, 256), Image.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                instance_num = getattr(dcm, 'InstanceNumber', 0)
                slice_images.append({
                    'instance_number': int(instance_num) if instance_num else 0,
                    'image': img_base64
                })
            except Exception as e:
                logger.warning(f"Failed to generate preview for {filepath}: {e}")
                continue
        
        # Sort slices by instance number
        slice_images.sort(key=lambda x: x['instance_number'])
        
        if slice_images:
            series_previews.append({
                'series_uid': series.series_uid,
                'series_description': series.series_description,
                'sequence_type': series.sequence_type,
                'modality': series.modality,
                'num_slices': len(slice_images),
                'slices': slice_images
            })
    
    logger.info(f"Generated previews for study {study_id}: {len(series_previews)} series")
    
    return {
        'study_id': study_id,
        'patient_id': study.patient_id,
        'study_date': study.study_date,
        'study_description': study.study_description,
        'series': series_previews
    }


@app.delete("/api/studies/{study_id}")
async def delete_study(study_id: str):
    """
    Delete a study and clean up files
    """
    if study_id not in studies_db:
        raise HTTPException(status_code=404, detail=f"Study {study_id} not found")
    
    # Cleanup files
    app.state.ingestor.cleanup_study(study_id)
    
    # Remove from database
    del studies_db[study_id]
    
    logger.info(f"🗑️ Study {study_id} deleted")
    
    return {"message": f"Study {study_id} deleted successfully"}


@app.get("/api/studies")
async def list_studies():
    """
    List all uploaded studies
    """
    studies_list = []
    for study_id, data in studies_db.items():
        studies_list.append({
            "study_id": study_id,
            "uploaded_at": data['uploaded_at'],
            "is_valid": data['validation'].is_valid,
            "has_results": data['result'] is not None,
            "num_series": len(data['study'].series)
        })
    
    return {
        "total_studies": len(studies_list),
        "studies": studies_list
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
