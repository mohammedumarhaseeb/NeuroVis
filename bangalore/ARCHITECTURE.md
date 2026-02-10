# System Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FileUpload   │  │ Validation   │  │ Analysis     │      │
│  │ Component    │  │ Status       │  │ Results      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│           │                │                 │               │
│           └────────────────┴─────────────────┘               │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTPS/REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  main.py (API Routes)                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        ▼                  ▼                  ▼              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐          │
│  │ ingest.py│      │parser.py │      │validate.py│         │
│  │          │      │          │      │          │          │
│  │ • Upload │      │ • DICOM  │      │ • Check  │          │
│  │ • Extract│─────▶│   parsing│─────▶│   modality│         │
│  │ • Filter │      │ • Group  │      │ • Verify │          │
│  │          │      │   series │      │   sequences│        │
│  └──────────┘      └──────────┘      │ • Count  │          │
│                                       │   slices │          │
│                                       └──────────┘          │
│                                             │                │
│                                   ┌─────────┴─────────┐      │
│                                   │   VALID? │                │
│                                   └─────────┬─────────┘      │
│                                        YES  │  NO            │
│                                             ▼                │
│                                   ┌──────────────────┐       │
│                                   │  ai_pipeline.py  │       │
│                                   │                  │       │
│                                   │ • Segmentation   │       │
│                                   │ • Genotype       │       │
│                                   │ • Explainability │       │
│                                   │ • Clinical Flags │       │
│                                   └──────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### Frontend Modules (Zero Medical Logic)

#### `FileUpload.tsx`
**Responsibilities:**
- Accept file uploads (drag-and-drop, file picker)
- Display selected files
- Send files to backend via `/api/upload`
- Show upload status and errors

**Does NOT:**
- Validate DICOM format
- Check medical requirements
- Parse DICOM headers

---

#### `ValidationStatus.tsx`
**Responsibilities:**
- Display validation results from backend
- Show required sequences status (checkmarks/X)
- List validation errors and warnings
- Enable/disable "Run Analysis" button based on validation
- Trigger inference via `/api/inference`

**Does NOT:**
- Perform validation logic
- Determine what sequences are required
- Check medical validity

---

#### `AnalysisResults.tsx`
**Responsibilities:**
- Display tumor volumes
- Show genotype probabilities as charts
- Render segmentation overlays
- Display attention maps
- Show clinical flags/warnings
- Export results as JSON

**Does NOT:**
- Interpret medical significance
- Make clinical decisions
- Modify analysis results

---

### Backend Modules (All Medical Intelligence)

#### `ingest.py` - File Handler
**Purpose:** Raw file processing (NO medical logic)

**Responsibilities:**
- Save uploaded files to disk
- Extract ZIP archives
- Filter files to find potential DICOM files (by extension or magic bytes)
- Return list of file paths

**Does NOT:**
- Validate DICOM structure
- Check modality
- Determine if study is complete

**Key Class:** `FileIngestor`

---

#### `parser.py` - DICOM Parser
**Purpose:** Extract metadata from DICOM files (NO validation)

**Responsibilities:**
- Read DICOM files using pydicom
- Extract: Modality, SeriesDescription, StudyUID, etc.
- Detect sequence type (T1, T1c, T2, FLAIR) from SeriesDescription
- Group DICOM files by SeriesInstanceUID
- Build `DicomStudy` object with organized series

**Does NOT:**
- Validate if modality is correct
- Check if study is complete
- Enforce medical requirements

**Key Class:** `DicomParser`
**Key Methods:**
- `read_dicom_file()` - Read single DICOM
- `detect_sequence_type()` - Pattern match on SeriesDescription
- `group_series()` - Group by SeriesInstanceUID
- `parse_study()` - Build complete DicomStudy object

---

#### `schemas.py` - Data Contracts
**Purpose:** Define data structures (NO logic)

**Key Models:**
- `DicomStudy` - Complete MRI study with series
- `DicomSeries` - Single MRI sequence
- `ValidationResult` - Validation outcome
- `TumorSegmentation` - Segmentation results
- `GenotypeIPrediction` - Genotype probabilities
- `ExplainabilityData` - Attention maps and explanations
- `ClinicalFlags` - Risk and urgency indicators
- `AnalysisResult` - Complete analysis output

---

#### `validate.py` - Medical Gatekeeper
**Purpose:** ENFORCE medical requirements (CRITICAL MODULE)

**Responsibilities:**
- Check modality is "MR" (not CT, X-ray, etc.)
- Verify all 4 required sequences present: T1, T1c, T2, FLAIR
- Verify each sequence has minimum 10 slices
- Return `ValidationResult` with:
  - `is_valid`: Boolean (pass/fail)
  - `errors`: List of blocking issues
  - `warnings`: Non-blocking concerns
  - `required_sequences`: Status dict

**Key Class:** `MedicalValidator`
**Key Method:** `validate_study(study: DicomStudy) -> ValidationResult`

**Validation Rules:**
```python
REQUIRED_SEQUENCES = [T1, T1c, T2, FLAIR]
MIN_SLICES_PER_SEQUENCE = 10
ALLOWED_MODALITY = "MR"
```

**This module determines if inference can proceed!**

---

#### `ai_pipeline.py` - AI Inference
**Purpose:** Run AI models on VALIDATED studies only

**Pipelines:**

1. **`TumorSegmentationPipeline`**
   - Segments tumor into regions (necrotic, edema, enhancing)
   - Calculates volumes in mL
   - Generates visualization overlay
   - Returns confidence score

2. **`GenotypePredictionPipeline`**
   - Predicts molecular markers:
     - IDH mutation status
     - MGMT promoter methylation
     - EGFR amplification
   - Returns probabilities and confidence

3. **`ExplainabilityPipeline`**
   - Generates attention/Grad-CAM maps
   - Identifies important features
   - Creates human-readable explanations

4. **`ClinicalFlaggingPipeline`**
   - Evaluates risk factors:
     - Large tumor volume
     - IDH-wildtype status
     - Significant necrosis
   - Sets urgency flags

**Note:** Currently uses `MockAIModel` for demo. Replace with real models (nnU-Net, trained classifiers) for production.

---

#### `main.py` - FastAPI Application
**Purpose:** REST API orchestration

**Endpoints:**

##### `POST /api/upload`
```
Input: Multipart form with DICOM/ZIP files
Process:
  1. FileIngestor.process_upload()
  2. DicomParser.parse_study()
  3. MedicalValidator.validate_study()
  4. Store study + validation in database
Output: { study_id, message, files_received }
```

##### `GET /api/validation/{study_id}`
```
Input: study_id
Output: ValidationResult with detailed status
```

##### `POST /api/inference`
```
Input: { study_id, run_segmentation, run_genotype_prediction, generate_explanations }
CRITICAL CHECK: if not validation.is_valid → return 422 error
Process:
  1. ✓ Check validation status (BLOCKS if invalid)
  2. Run TumorSegmentationPipeline
  3. Run GenotypePredictionPipeline
  4. Run ExplainabilityPipeline
  5. Run ClinicalFlaggingPipeline
  6. Store AnalysisResult
Output: Complete AnalysisResult
```

##### `GET /api/results/{study_id}`
```
Input: study_id
Output: AnalysisResult (or validation status if not yet analyzed)
```

---

## Data Flow

### Upload Flow
```
User uploads files
      ↓
Frontend FileUpload component
      ↓
POST /api/upload
      ↓
ingest.py: Save + extract files
      ↓
ingest.py: Filter DICOM files
      ↓
parser.py: Read DICOM headers
      ↓
parser.py: Group by series
      ↓
parser.py: Detect sequence types
      ↓
parser.py: Build DicomStudy
      ↓
validate.py: Check modality
      ↓
validate.py: Check required sequences
      ↓
validate.py: Check slice counts
      ↓
validate.py: Return ValidationResult
      ↓
Store study + validation
      ↓
Return study_id to frontend
```

### Inference Flow
```
User clicks "Run Analysis"
      ↓
Frontend ValidationStatus component
      ↓
POST /api/inference
      ↓
Retrieve study from database
      ↓
⚠️  CHECK VALIDATION ⚠️
   if not valid → 422 Error (BLOCKED)
   if valid → proceed
      ↓
ai_pipeline: Tumor Segmentation
      ↓
ai_pipeline: Genotype Prediction
      ↓
ai_pipeline: Generate Explanations
      ↓
ai_pipeline: Evaluate Clinical Flags
      ↓
Assemble AnalysisResult
      ↓
Store result in database
      ↓
Return AnalysisResult to frontend
```

---

## Safety Mechanisms

### 1. Validation Gatekeeper
**Location:** `validate.py` + `main.py` (line ~185)

```python
# MEDICAL VALIDATION GATE
if not validation.is_valid:
    logger.warning(f"⛔ Inference BLOCKED - validation failed")
    raise HTTPException(status_code=422, detail={...})
```

**Effect:** AI inference CANNOT run on invalid studies

### 2. Frontend Enforcement
**Location:** `ValidationStatus.tsx`

```typescript
<button
  onClick={runInference}
  disabled={!isValid || running}  // Disabled if invalid
  ...
```

**Effect:** UI prevents users from triggering inference on invalid studies

### 3. Clear Error Messages
All validation errors include:
- What is wrong
- Why it's required
- Medical context

Example:
```
"Missing required sequence: T1c. Brain tumor analysis requires 
T1, T1c (T1 with contrast), T2, and FLAIR sequences."
```

---

## Explainability Features

### 1. Attention Maps
- Heatmaps showing which regions the model focused on
- Provided per sequence (T1c, T2, FLAIR)
- Base64-encoded PNGs for frontend display

### 2. Important Features
- List of key features influencing the prediction
- Examples:
  - "Large enhancing tumor component"
  - "T1c enhancement pattern"
  - "Tumor heterogeneity index"

### 3. Human-Readable Explanations
- Natural language summary of findings
- Combines segmentation and genotype information
- Example:
  ```
  "Tumor identified with total volume of 45.2 mL. 
   Enhancing component: 12.3 mL. Predicted genotype: 
   IDH-wildtype (probability: 78.5%). MGMT promoter 
   methylation likely (probability: 65.2%)."
  ```

---

## Clinical Decision Support

### Risk Factors Evaluated
1. **Tumor Size:** > 50 mL = high risk
2. **Enhancement:** > 20 mL enhancing = high risk
3. **Necrosis:** > 10 mL necrotic = urgent review
4. **IDH Status:** IDH-wildtype > 70% = high risk
5. **EGFR:** Amplification > 60% = high risk

### Urgency Flags
- **High Risk:** Displays warning banner
- **Requires Urgent Review:** Highlights in red, shows reason
- **Risk Factors:** Listed for clinical context

---

## Extensibility Points

### Adding New Sequences
Edit `schemas.py`:
```python
class MRISequenceType(str, Enum):
    T1 = "T1"
    T1C = "T1c"
    T2 = "T2"
    FLAIR = "FLAIR"
    DWI = "DWI"  # NEW
```

Edit `parser.py`:
```python
SEQUENCE_KEYWORDS = {
    ...
    MRISequenceType.DWI: ['dwi', 'diffusion']
}
```

Edit `validate.py`:
```python
REQUIRED_SEQUENCES = [
    MRISequenceType.T1,
    ...
    MRISequenceType.DWI  # Add if required
]
```

### Adding New Validation Rules
Edit `validate.py`, add new method:
```python
def validate_contrast_timing(self, study: DicomStudy):
    # Custom validation logic
    pass
```

Call from `validate_study()`:
```python
def validate_study(self, study: DicomStudy):
    ...
    timing_valid, timing_errors = self.validate_contrast_timing(study)
    all_errors.extend(timing_errors)
```

### Adding New AI Models
Edit `ai_pipeline.py`:
```python
class RealSegmentationModel:
    def __init__(self, model_path):
        self.model = load_model(model_path)
    
    def segment_tumor(self, study: DicomStudy):
        # Real inference logic
        pass
```

Replace in `main.py`:
```python
app.state.ai_model = RealSegmentationModel('path/to/model')
```

---

## Performance Considerations

### Current (Mock Models)
- Upload: < 1 second (depends on file size)
- Validation: < 100 ms
- Inference: ~1 second (mock delay)
- **Total:** ~2-3 seconds end-to-end

### Production (Real Models)
- Upload: 1-5 seconds (larger files)
- Validation: < 100 ms (unchanged)
- Segmentation: 30-60 seconds (nnU-Net on GPU)
- Genotype Prediction: 10-30 seconds
- Explainability: 5-15 seconds
- **Total:** ~60-120 seconds end-to-end

**Optimization strategies:**
- GPU acceleration (CUDA)
- Model quantization
- Async processing with job queue
- Caching intermediate results
- Batch processing multiple studies

---

## Security Considerations

### Current Implementation
- CORS: Allow all origins (development)
- No authentication
- No rate limiting
- Files stored locally
- In-memory database

### Production Requirements
1. **Authentication:** JWT tokens, OAuth
2. **Authorization:** Role-based access control
3. **Rate Limiting:** Prevent abuse
4. **Input Validation:** Strict file type checking
5. **Secure Storage:** Encrypted DICOM storage
6. **HIPAA Compliance:** If handling PHI
7. **Audit Logging:** Track all access
8. **HTTPS:** TLS/SSL encryption
9. **CORS:** Restrict to known frontends
10. **Database:** PostgreSQL with encryption

---

## Monitoring & Observability

### Recommended Tools
- **Application Monitoring:** Sentry, Datadog
- **Logging:** ELK stack (Elasticsearch, Logstash, Kibana)
- **Metrics:** Prometheus + Grafana
- **Tracing:** Jaeger, OpenTelemetry

### Key Metrics to Track
- Upload success rate
- Validation pass/fail ratio
- Inference latency (p50, p95, p99)
- Error rates by endpoint
- Model confidence distributions
- Clinical flag frequency

---

## Testing Strategy

### Unit Tests
- `test_ingest.py`: File handling, ZIP extraction
- `test_parser.py`: DICOM parsing, sequence detection
- `test_validate.py`: Validation rules
- `test_ai_pipeline.py`: AI pipeline components

### Integration Tests
- End-to-end upload → validation → inference flow
- API endpoint tests
- Error handling tests

### Test Data
Use `create_test_data.py` to generate:
- Valid studies (all sequences)
- Invalid studies (missing sequences)
- Edge cases (minimum slices, etc.)

---

## Deployment Architecture

### Recommended Setup

```
Internet
    ↓
Load Balancer (NGINX)
    ↓
    ├─→ Frontend (Vercel/Netlify)
    └─→ Backend API (Docker + Gunicorn)
            ↓
         GPU Instance (for AI models)
            ↓
         PostgreSQL Database
            ↓
         S3/Cloud Storage (DICOM files)
```

### Docker Deployment

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```

**docker-compose.yml:**
```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
```

---

## Conclusion

This architecture provides:
- ✅ **Strict separation of concerns**
- ✅ **Medical validation gatekeeper**
- ✅ **Modular, extensible design**
- ✅ **Explainable AI**
- ✅ **Clinical decision support**
- ✅ **Demo-ready interface**

The system is designed to be safe, maintainable, and production-ready with real AI model integration.
