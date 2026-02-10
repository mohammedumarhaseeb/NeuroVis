# Demo Script - Brain Tumor MRI Analysis System

## 🎯 Demo Setup (5 minutes before presentation)

### Prerequisites
1. Backend running on `http://localhost:8000`
2. Frontend running on `http://localhost:3000`
3. Test data generated (`test_data/` and `test_data_invalid/`)
4. Browser ready with multiple tabs
5. Terminal windows visible (optional, for logs)

### Quick Checklist
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
# ✓ Should see: "🚀 Starting Brain Tumor MRI Analysis API"

# Terminal 2: Frontend
cd frontend
npm run dev
# ✓ Should see: "- Local: http://localhost:3000"

# Terminal 3: Test Data
cd backend
python create_test_data.py
# ✓ Should create test_data/ and test_data_invalid/
```

---

## 📢 Demo Flow (10-15 minutes)

### Part 1: Introduction (2 minutes)

**Opening Statement:**
> "I'm presenting a medical AI system for brain tumor MRI analysis. The key innovation is **validation-gated inference** - the system acts as a medical gatekeeper, checking studies before allowing AI to run. This prevents misleading predictions from incomplete data."

**System Overview:**
> "The system has two parts:
> 1. **Backend (Python/FastAPI)** - Contains ALL medical intelligence
> 2. **Frontend (Next.js)** - Zero medical logic, pure visualization
> 
> This strict separation ensures medical rules live in one place."

**Screen:** Show architecture diagram or system overview

---

### Part 2: Demo - Invalid Study (4 minutes)

**Narrative:**
> "First, let me show what happens when doctors upload an incomplete study. This simulates a real-world scenario where MRI sequences might be missing."

**Steps:**

1. **Open Frontend** (`http://localhost:3000`)
   - Point out clean interface
   - Highlight "Brain Tumor MRI Analysis" title

2. **Upload Invalid Study**
   ```
   - Click file upload or drag-and-drop
   - Select entire `test_data_invalid/` folder
     (or ZIP it first: test_data_invalid.zip)
   - Click "Upload and Validate"
   ```

3. **Show Validation Failure**
   - ✗ Red banner appears: "Validation FAILED"
   - Point out specific error:
     ```
     "Missing required sequence: T1c. Brain tumor analysis 
     requires T1, T1c (T1 with contrast), T2, and FLAIR sequences."
     ```
   - Show required sequences grid:
     - T1: ✓ (green)
     - T1c: ✗ (gray)
     - T2: ✓ (green)
     - FLAIR: ✓ (green)

4. **Highlight Safety Feature**
   - Point to "Run AI Analysis" button
   - Show it's **disabled and grayed out**
   > "The system blocks inference completely. The AI won't run on bad data."

5. **Show Error Message**
   - Read the validation error aloud
   - Emphasize clarity:
     ```
     "Not just 'invalid' - it tells you exactly what's missing 
     and why it's needed."
     ```

**Key Talking Points:**
- ✅ Validation happens **before** inference
- ✅ **Clear, human-readable** error messages
- ✅ Medical knowledge **enforced by code**
- ✅ Frontend respects backend validation (button disabled)

---

### Part 3: Demo - Valid Study (4 minutes)

**Narrative:**
> "Now let's upload a complete study with all required sequences. This is what the system is designed for."

**Steps:**

1. **Upload Valid Study**
   ```
   - Scroll up or open new upload section
   - Select entire `test_data/` folder
     (or test_data.zip)
   - Click "Upload and Validate"
   ```

2. **Show Validation Success**
   - ✓ Green banner appears: "Validation PASSED"
   - All sequences have green checkmarks:
     - T1: ✓
     - T1c: ✓
     - T2: ✓
     - FLAIR: ✓
   - Show validation summary:
     ```
     "✓ Study validation PASSED. All required sequences present. 
     Ready for AI analysis."
     ```

3. **Enable Inference**
   - Point to "Run AI Analysis" button
   - Show it's now **enabled and blue**
   > "The system gives us the green light. AI can proceed safely."

4. **Trigger Inference**
   - Click "Run AI Analysis"
   - Show loading state: "Running AI Analysis..."
   - Wait ~1-2 seconds (mock models)

**Optional:** If terminals are visible, point out backend logs:
```
Running tumor segmentation...
Running genotype prediction...
Generating explanations...
✓ Inference complete (processing time)
```

---

### Part 4: Results & Explainability (4 minutes)

**Narrative:**
> "The system provides a complete analysis with built-in explainability. Let's walk through the results."

**Steps:**

1. **Tumor Segmentation**
   - Point out three colored cards:
     - **Whole Tumor Volume:** 45.2 mL (purple)
     - **Enhancing Tumor:** 12.3 mL (yellow)
     - **Necrotic Core:** 8.1 mL (red)
   - Show segmentation confidence: "92.3%"
   - Point to segmentation overlay image:
     ```
     "This shows where the AI found the tumor. 
     Red = necrotic, Green = edema, Yellow = enhancing."
     ```

2. **Genotype Prediction**
   - Show probability bars:
     - IDH Mutation: 35.2%
     - IDH Wildtype: 64.8%
     - MGMT Methylation: 58.3%
     - EGFR Amplification: 42.1%
   - Emphasize: "These are **probabilities**, not certainties"
   - Show prediction confidence: "85.7%"

3. **Explainability**
   - Read explanation text:
     ```
     "Tumor identified with total volume of 45.2 mL. 
     Predicted genotype: IDH-wildtype (probability: 64.8%). 
     MGMT promoter methylation likely (probability: 58.3%)."
     ```
   - Point to important features tags:
     - "Large enhancing tumor component"
     - "T1c enhancement pattern"
     - "Tumor location in detected region"
   - Show attention maps:
     ```
     "These heatmaps show which brain regions the AI 
     focused on for each MRI sequence. Brighter areas 
     = more important for the prediction."
     ```

4. **Clinical Flags (if triggered)**
   - If high-risk flags appear:
     ```
     ⚠️ Clinical Attention Required
     High Risk: This study shows high-risk indicators
     Risk Factors:
     • Large tumor volume (>50 mL)
     • IDH-wildtype (worse prognosis)
     ```

5. **Download Report**
   - Click "Download Report" button
   - Show JSON file downloads
   - Mention: "All results exportable for documentation"

**Key Talking Points:**
- ✅ **Comprehensive results:** segmentation + genotype + confidence
- ✅ **Explainable:** attention maps show AI's reasoning
- ✅ **Actionable:** clinical flags highlight urgent cases
- ✅ **Exportable:** JSON for integration with EHR systems

---

### Part 5: API & Architecture (2 minutes)

**Narrative:**
> "Let me quickly show the backend architecture to emphasize the safety design."

**Steps:**

1. **Show API Documentation** (optional)
   - Open new tab: `http://localhost:8000/docs`
   - Show Swagger/OpenAPI interface
   - Point out key endpoints:
     - `POST /api/upload` - Upload + validate
     - `GET /api/validation/{study_id}` - Check status
     - `POST /api/inference` - Run AI (blocks if invalid)

2. **Explain Module Separation**
   - Show file structure (if using IDE):
     ```
     backend/
     ├── ingest.py      → File handling (no medical logic)
     ├── parser.py      → DICOM parsing (no validation)
     ├── validate.py    → MEDICAL GATEKEEPER ⚠️
     ├── ai_pipeline.py → AI inference (only on valid studies)
     └── main.py        → API (enforces validation)
     ```
   
   - Key point:
     > "validate.py is the single source of truth for medical requirements. 
     > If it says 'invalid,' nothing gets through."

3. **Show Code (optional, if time)**
   - Open `main.py`, scroll to inference endpoint (~line 185):
     ```python
     # MEDICAL VALIDATION GATE
     if not validation.is_valid:
         logger.warning(f"⛔ Inference BLOCKED")
         raise HTTPException(status_code=422, ...)
     ```
   - Emphasize:
     > "This is enforced at the API level. Even if someone bypasses 
     > the frontend, the backend will reject invalid studies."

---

### Part 6: Wrap-Up (1 minute)

**Summary Statement:**
> "In summary, this system demonstrates three key innovations:
> 
> 1. **Validation-Gated Inference** - AI only runs on complete, valid studies
> 2. **Explainability by Design** - Every prediction comes with reasoning
> 3. **Separation of Concerns** - Medical logic stays in backend, frontend is pure UI
> 
> This makes the system safe, maintainable, and production-ready."

**Future Enhancements:**
> "To productionize this:
> 1. Replace mock models with real nnU-Net for segmentation
> 2. Train genotype classifiers on real patient data
> 3. Add authentication and HIPAA compliance
> 4. Deploy with GPU infrastructure
> 5. Integrate with hospital PACS/EHR systems"

**Closing:**
> "Questions?"

---

## 🎤 Common Q&A

### Q: "What if a doctor really wants to run the AI on an incomplete study?"
**A:** 
> "That's a great question. The current design blocks incomplete studies completely, but we could add a 'Force Analyze (Advanced Mode)' option with:
> - Big warning banner
> - Require doctor credentials
> - Log the override for audit
> - Show reduced confidence in results
> 
> But for safety, the default is to block."

### Q: "How accurate are the AI models?"
**A:**
> "Currently, these are mock models for demonstration. In production, we'd use:
> - nnU-Net for segmentation (SOTA for medical imaging)
> - Trained classifiers on validated datasets (BraTS, TCGA)
> - Clinical validation studies to establish accuracy benchmarks
> 
> Typical targets: 85-95% Dice score for segmentation, 75-85% AUC for genotype prediction."

### Q: "How long does analysis take?"
**A:**
> "With mock models: ~1-2 seconds. With real models on GPU:
> - Segmentation: 30-60 seconds
> - Genotype prediction: 10-30 seconds
> - Total: ~1-2 minutes
> 
> That's fast enough for clinical use, especially compared to manual analysis (hours to days)."

### Q: "What about CT scans or other modalities?"
**A:**
> "The system currently only accepts MRI (Modality: MR). If you upload CT scans, validation will fail with:
> 
> 'Invalid modality: CT. Expected MR for MRI. This system only accepts MRI studies.'
> 
> We could extend to CT by:
> - Adding CT-specific validation rules
> - Training separate CT-specific models
> - Keeping the same gatekeeper architecture"

### Q: "How do you handle patient privacy?"
**A:**
> "Great question. For production:
> 1. DICOM anonymization before upload
> 2. Encrypted storage (at rest and in transit)
> 3. Access logging and audit trails
> 4. HIPAA compliance framework
> 5. Data retention policies
> 6. No PHI in frontend logs
> 
> For this demo, we use synthetic data only."

### Q: "Can this replace radiologists?"
**A:**
> "No. This is a **decision support tool**, not a replacement. The workflow is:
> 
> 1. AI analyzes MRI → generates predictions
> 2. Radiologist reviews AI results + original images
> 3. Radiologist makes final diagnosis
> 4. AI serves as a 'second opinion' or efficiency boost
> 
> The disclaimer screen makes this clear: 'Must be reviewed by qualified medical professionals.'"

---

## 🔧 Troubleshooting During Demo

### Issue: "Frontend won't load"
**Fix:**
```bash
cd frontend
npm run dev
# Check http://localhost:3000
```

### Issue: "Upload fails / API not responding"
**Fix:**
```bash
cd backend
python main.py
# Check http://localhost:8000
```

### Issue: "Validation passed but inference fails"
**Check:**
- Backend logs for errors
- Ensure mock models initialized
- Restart backend

### Issue: "Test data not found"
**Fix:**
```bash
cd backend
python create_test_data.py
# Creates test_data/ and test_data_invalid/
```

---

## 📊 Demo Metrics to Highlight

- **Upload time:** < 1 second
- **Validation time:** < 100ms
- **Inference time:** ~1-2 seconds (mock) / 60-120s (real)
- **Number of files:** 80 DICOM files (20 slices × 4 sequences)
- **Validation rules:** 3 main checks (modality, sequences, slice count)
- **AI outputs:** 4 components (segmentation, genotype, explainability, flags)

---

## 🎯 Key Differentiators to Emphasize

1. **Validation Before Inference**
   - Most AI tools blindly run on any input
   - This system checks medical validity first
   - Prevents garbage-in-garbage-out scenarios

2. **Explainability Built-In**
   - Not a "black box"
   - Attention maps show AI's focus
   - Human-readable explanations
   - Important features listed

3. **Clinical Safety Features**
   - High-risk flags
   - Urgency detection
   - Risk factor enumeration
   - Conservative by design

4. **Modular Architecture**
   - Each module has one job
   - Easy to update validation rules
   - Easy to swap AI models
   - Frontend/backend separation

5. **Demo-Ready UI**
   - Clean, modern design
   - Clear error messages
   - Real-time feedback
   - Exportable results

---

## 📝 Post-Demo Follow-Up

### Materials to Share
1. **README.md** - Full documentation
2. **SETUP.md** - Quick start guide
3. **ARCHITECTURE.md** - Deep dive on design
4. **GitHub repository** (if hosted)
5. **Demo video/recording**

### Next Steps
1. Gather feedback
2. Identify production requirements
3. Plan real AI model integration
4. Discuss deployment strategy
5. Consider additional features

---

**Good luck with your demo! 🚀**

Remember: The key message is **safety through validation**. Everything else supports this core value proposition.
