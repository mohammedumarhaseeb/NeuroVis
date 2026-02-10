# Brain Tumor MRI Analysis - Quick Setup Guide

## Prerequisites

Before starting, ensure you have:
- **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 18+** installed ([Download](https://nodejs.org/))
- **pip** (comes with Python)
- **npm** (comes with Node.js)

Check your versions:
```bash
python --version  # or python3 --version
node --version
npm --version
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```batch
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

This will:
1. Create Python virtual environment
2. Install all dependencies
3. Start backend and frontend servers automatically

### Option 2: Manual Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

Backend will run at `http://localhost:8000`

#### Frontend Setup (in a new terminal)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at `http://localhost:3000`

## 🧪 Creating Test Data

To test the system, generate mock DICOM files:

```bash
cd backend
python create_test_data.py
```

This creates:
- `test_data/` - Valid study (PASSES validation)
- `test_data_invalid/` - Incomplete study (FAILS validation)

## 📖 Using the System

### 1. Upload MRI Study
- Open `http://localhost:3000` in your browser
- Drag and drop DICOM files or click to browse
- Or upload the entire `test_data` folder as ZIP

### 2. View Validation Status
- System automatically validates the study
- Green checkmarks = all required sequences present
- Red X = validation failed with specific errors

### 3. Run AI Analysis
- Click "Run AI Analysis" button (only enabled if validation passes)
- Wait for processing (~1-2 seconds with mock models)

### 4. Review Results
- Tumor segmentation with volumes
- Genotype predictions with probabilities
- Attention maps showing model focus areas
- Clinical flags for high-risk cases
- Download JSON report

## 🔍 API Testing

Test the API directly with curl or Postman:

```bash
# Health check
curl http://localhost:8000/

# Upload files (replace with actual file paths)
curl -X POST http://localhost:8000/api/upload \
  -F "files=@test_data/t1_001.dcm" \
  -F "files=@test_data/t1c_001.dcm"

# Check validation (replace STUDY_ID)
curl http://localhost:8000/api/validation/{STUDY_ID}

# Run inference
curl -X POST http://localhost:8000/api/inference \
  -H "Content-Type: application/json" \
  -d '{"study_id": "STUDY_ID", "run_segmentation": true, "run_genotype_prediction": true, "generate_explanations": true}'

# Get results
curl http://localhost:8000/api/results/{STUDY_ID}
```

## 🐛 Troubleshooting

### Backend won't start
- **Port 8000 already in use**: Kill the process or change port in `main.py`
- **Module not found**: Ensure virtual environment is activated and dependencies installed
- **Permission denied**: On Linux/Mac, you may need `sudo` or check file permissions

### Frontend won't start
- **Port 3000 already in use**: Kill the process or change port with `npm run dev -- -p 3001`
- **Module not found**: Run `npm install` again
- **API connection failed**: Ensure backend is running on port 8000

### File upload fails
- **File too large**: Check FastAPI settings (default: 200MB limit)
- **Invalid DICOM**: Ensure files are valid DICOM format
- **ZIP extraction fails**: Check ZIP is not corrupted

### Validation always fails
- **Missing sequences**: Study must have T1, T1c, T2, and FLAIR
- **Wrong modality**: Files must be MRI (Modality: MR), not CT or X-ray
- **Too few slices**: Each sequence needs 10+ slices

## 📦 Project Structure

```
bangalore/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ingest.py            # File upload handling
│   ├── parser.py            # DICOM parsing
│   ├── validate.py          # Medical validation
│   ├── ai_pipeline.py       # AI inference
│   ├── schemas.py           # Data models
│   ├── requirements.txt     # Python dependencies
│   └── create_test_data.py  # Test data generator
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app directory
│   │   └── components/      # React components
│   ├── package.json         # Node dependencies
│   └── next.config.js       # Next.js config
├── README.md                # Full documentation
├── SETUP.md                 # This file
├── start.bat                # Windows startup script
└── start.sh                 # Linux/Mac startup script
```

## 🎯 Demo Flow

1. **Demo Invalid Study**:
   - Upload `test_data_invalid/`
   - Show validation rejection
   - Point out missing T1c sequence
   - "Run Analysis" button is disabled

2. **Demo Valid Study**:
   - Upload `test_data/`
   - All sequences show green checkmarks
   - Click "Run AI Analysis"
   - Show results with explanations

3. **Show Features**:
   - Tumor volume measurements
   - Genotype probabilities
   - Attention maps
   - Clinical flags (if triggered)
   - Download report

## 🔧 Configuration

### Backend Configuration
- **Upload directory**: Edit `ingest.py` or set via environment variable
- **API port**: Change in `main.py` (default: 8000)
- **CORS origins**: Configure in `main.py` for production

### Frontend Configuration
- **API URL**: Edit `frontend/.env.local`:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
- **Frontend port**: Change with `npm run dev -- -p PORT`

## 📚 Next Steps

### For Production:
1. Replace mock AI models with real pretrained models (nnU-Net, etc.)
2. Add authentication and authorization
3. Implement database storage (PostgreSQL/Redis)
4. Deploy with Docker/Kubernetes
5. Add monitoring and logging (Sentry, CloudWatch)
6. Implement HIPAA compliance measures

### For Development:
1. Add unit tests (pytest for backend, Jest for frontend)
2. Add integration tests
3. Implement CI/CD pipeline
4. Add code quality tools (black, pylint, ESLint)
5. Create API documentation with Swagger/OpenAPI

## 💡 Tips

- **Use Chrome/Firefox**: Best compatibility with the UI
- **Check browser console**: For frontend debugging
- **Check terminal logs**: Backend shows detailed processing logs
- **Start fresh**: Delete `mri_uploads_*` folders to clear old data
- **API docs**: Visit `http://localhost:8000/docs` for interactive API documentation

## 📞 Support

For issues or questions:
1. Check the main `README.md` for detailed documentation
2. Review error messages in browser console and terminal
3. Ensure all prerequisites are installed correctly
4. Try the automated setup script first

## ⚠️ Important Notes

- This is a **research prototype** - not for clinical use
- Mock AI models are used for demonstration
- All data is stored temporarily (deleted on restart)
- DICOM files may be large - ensure sufficient disk space
- Processing times shown are with mock models (real models will be slower)

---

**Ready to go!** Open `http://localhost:3000` and start analyzing brain MRI scans! 🧠
