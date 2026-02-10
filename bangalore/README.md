# Brain Tumor MRI Analysis System

A hackathon-grade, end-to-end AI system for brain tumor MRI analysis with genotype-aware clinical decision support. Built with strict separation of concerns, safety-by-design validation, and explainability.

## 🎯 Key Features

- **Medical Validation Gatekeeper**: Validates MRI studies before allowing AI inference
- **Tumor Segmentation**: 3D segmentation with volume measurements
- **Disease Severity Heatmap**: Visual representation of abnormality distribution and intensity
- **Genotype Prediction**: IDH mutation, MGMT methylation, EGFR amplification
- **Explainability**: Attention maps and feature importance
- **Clinical Flags**: Automatic risk assessment and urgency detection
- **Modern UI**: Clean, intuitive interface with real-time feedback

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **`ingest.py`**: File upload and extraction (no medical logic)
- **`parser.py`**: DICOM header parsing and series grouping
- **`schemas.py`**: Data contracts and models
- **`validate.py`**: Medical validation gatekeeper
- **`ai_pipeline.py`**: Tumor segmentation, genotype prediction, explainability
- **`main.py`**: FastAPI REST API

### Frontend (Next.js/React)
- **Upload Interface**: Drag-and-drop DICOM/ZIP upload
- **Validation Display**: Clear accept/reject with reasons
- **Results Visualization**: Segmentation overlays, probability charts
- **Report Download**: JSON export of analysis results

## 🚀 Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the API
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The UI will be available at `http://localhost:3000`

## 📡 API Endpoints

### `POST /api/upload`
Upload MRI study (DICOM files or ZIP). Returns `study_id` and validates immediately.

**Request**: Multipart form data with files
**Response**:
```json
{
  "study_id": "uuid",
  "message": "Study uploaded and validated successfully",
  "files_received": 4
}
```

### `GET /api/validation/{study_id}`
Get detailed validation status for a study.

**Response**:
```json
{
  "study_id": "uuid",
  "validation": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "required_sequences": {
      "T1": true,
      "T1c": true,
      "T2": true,
      "FLAIR": true
    }
  },
  "summary": "✓ Study validation PASSED..."
}
```

### `POST /api/inference`
Run AI inference on a validated study. **Blocks if validation failed**.

**Request**:
```json
{
  "study_id": "uuid",
  "run_segmentation": true,
  "run_genotype_prediction": true,
  "generate_explanations": true
}
```

**Response**: Full `AnalysisResult` with segmentation, genotype, explainability, and clinical flags.

### `GET /api/results/{study_id}`
Retrieve analysis results.

### `GET /api/studies`
List all uploaded studies.

### `DELETE /api/studies/{study_id}`
Delete a study and clean up files.

## 🔒 Safety Features

### 1. Validation Gatekeeper
- **Enforced at API level**: `/api/inference` returns 422 if validation fails
- **No blind inference**: AI models only run on validated studies
- **Clear error messages**: Specific reasons for rejection

### 2. Required Validation Checks
- ✓ Modality must be MRI (not CT, X-ray, etc.)
- ✓ All 4 sequences present: T1, T1c, T2, FLAIR
- ✓ Minimum slice count (10+ per sequence)
- ✓ Warns if slice count is low (< 20)

### 3. Explainability
- Attention/Grad-CAM heatmaps show where model looked
- Important features listed
- Human-readable explanations

### 4. Clinical Flags
- **High Risk**: Large tumor, IDH-wildtype, EGFR amplification
- **Urgent Review**: Large necrotic core, aggressive features
- **Risk Factors**: Listed explicitly

## 🧪 Testing with Sample Data

### Create Mock DICOM Files

```python
import pydicom
from pydicom.dataset import Dataset, FileDataset
import numpy as np
from datetime import datetime

def create_mock_dicom(filename, series_desc, series_uid, modality="MR"):
    file_meta = Dataset()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    ds.PatientID = "TEST001"
    ds.StudyInstanceUID = "1.2.3.4.5.6.7.8.9"
    ds.SeriesInstanceUID = series_uid
    ds.SOPInstanceUID = f"{series_uid}.1"
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
    ds.Modality = modality
    ds.SeriesDescription = series_desc
    ds.StudyDate = datetime.now().strftime('%Y%m%d')
    ds.InstanceNumber = 1
    
    # Add pixel data
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 256
    ds.Columns = 256
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.PixelData = np.random.randint(0, 4096, (256, 256), dtype=np.uint16).tobytes()
    
    ds.save_as(filename)
    print(f"Created {filename}")

# Create test files
create_mock_dicom("t1.dcm", "T1-weighted", "1.2.3.100")
create_mock_dicom("t1c.dcm", "T1-weighted post contrast", "1.2.3.200")
create_mock_dicom("t2.dcm", "T2-weighted", "1.2.3.300")
create_mock_dicom("flair.dcm", "FLAIR", "1.2.3.400")
```

Save as `create_test_data.py` and run to generate test DICOM files.

## 📊 System Flow

```
1. User uploads DICOM files/ZIP
   ↓
2. ingest.py extracts and filters files
   ↓
3. parser.py reads DICOM headers and groups series
   ↓
4. validate.py checks medical requirements ⚠️ GATEKEEPER
   ↓
5. If VALID → Enable inference button
   If INVALID → Show errors, block inference
   ↓
6. User triggers inference
   ↓
7. ai_pipeline.py runs:
   - Tumor segmentation
   - Genotype prediction
   - Explainability generation
   ↓
8. Clinical flags evaluated
   ↓
9. Results displayed + downloadable
```

## 🎨 Frontend Components

### `FileUpload.tsx`
- Drag-and-drop file upload
- Supports multiple DICOM files and ZIP
- Shows selected files before upload
- Error handling with clear messages

### `ValidationStatus.tsx`
- Displays validation results
- Shows all required sequences with status
- Lists errors and warnings
- **Blocks "Run Analysis" button if invalid**
- Triggers inference on validated studies

### `AnalysisResults.tsx`
- Tumor volume measurements with color coding
- Genotype probability bars
- Attention maps visualization
- Clinical flags/warnings highlighted
- Download report button

## 🔧 Configuration

### Backend
- Edit upload directory in `ingest.py` or set via environment
- Model paths in `ai_pipeline.py` (currently using mock models)
- CORS origins in `main.py`

### Frontend
- API URL in `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

## 🚨 Production Considerations

### Replace Mock AI Models
Current system uses `MockAIModel` for demonstration. For production:

1. **Segmentation**: Replace with nnU-Net, DeepMedic, or similar
2. **Genotype Prediction**: Train classifier on tumor ROI features
3. **Explainability**: Implement Grad-CAM or SHAP

```python
# In ai_pipeline.py
class RealAIModel:
    def __init__(self):
        self.seg_model = load_segmentation_model('path/to/nnunet')
        self.genotype_model = load_genotype_model('path/to/classifier')
```

### Database
Replace in-memory `studies_db` with:
- Redis for session storage
- PostgreSQL for persistent storage
- S3/Cloud Storage for DICOM files

### Security
- Add authentication (JWT tokens)
- Rate limiting
- Input validation
- Secure file handling
- HIPAA compliance (if handling real PHI)

### Deployment
- **Backend**: Docker + Gunicorn + NGINX
- **Frontend**: Vercel or similar
- **GPU**: For real AI models (CUDA support)

## 📝 Code Quality

- **Type hints**: Python type annotations throughout
- **Pydantic models**: Strict data validation
- **Logging**: Comprehensive logging at all levels
- **Error handling**: Graceful failures with clear messages
- **Separation of concerns**: Each module has single responsibility

## 🎯 Hackathon Demo Script

1. **Upload Invalid Study** (e.g., missing T1c)
   - Show validation rejection
   - Highlight clear error messages
   - Demonstrate "Run Analysis" button is disabled

2. **Upload Valid Study**
   - Show validation success
   - All sequences green checkmarks
   - Enable "Run Analysis"

3. **Run Inference**
   - Show progress indicator
   - Display results in real-time

4. **Explore Results**
   - Point out tumor volumes
   - Show genotype probabilities
   - Explain attention maps
   - Highlight clinical flags if present

5. **Download Report**
   - Export JSON for documentation

## 📜 License

This is a hackathon demonstration project. For research use only.

## ⚠️ Disclaimer

This system is a research prototype and should NOT be used for clinical decision-making without proper validation, regulatory approval, and oversight by qualified medical professionals.

---

**Built with ❤️ for the hackathon**
