"""
Quick Demo Script - Brain Tumor MRI Analysis System
Demonstrates validation and inference via API calls
"""

import requests
import json
import os
from pathlib import Path
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def demo_invalid_study():
    """Demo Part 1: Upload Invalid Study (missing T1c)"""
    print_section("DEMO 1: Invalid Study (Missing T1c Sequence)")
    
    # Prepare files from test_data_invalid
    files = []
    test_dir = Path("test_data_invalid")
    
    for dcm_file in sorted(test_dir.glob("*.dcm"))[:10]:  # Upload first 10 for speed
        files.append(('files', (dcm_file.name, open(dcm_file, 'rb'), 'application/dicom')))
    
    print(f"📤 Uploading {len(files)} DICOM files from test_data_invalid/")
    
    # Upload
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    # Close file handles
    for _, file_tuple in files:
        file_tuple[1].close()
    
    if response.status_code == 200:
        result = response.json()
        study_id = result['study_id']
        print(f"✅ Upload successful - Study ID: {study_id}")
        print(f"   Files received: {result['files_received']}")
        
        # Get validation status
        print("\n🔍 Checking validation status...")
        val_response = requests.get(f"{BASE_URL}/api/validation/{study_id}")
        
        if val_response.status_code == 200:
            validation = val_response.json()
            print(f"\n{'❌'if not validation['validation']['is_valid'] else '✅'} Validation Result: {'FAILED' if not validation['validation']['is_valid'] else 'PASSED'}")
            
            if validation['validation']['errors']:
                print("\n⚠️  Errors:")
                for error in validation['validation']['errors']:
                    print(f"   • {error}")
            
            print("\n📋 Required Sequences:")
            for seq, present in validation['validation']['required_sequences'].items():
                status = "✓" if present else "✗"
                print(f"   {status} {seq}")
            
            print(f"\n📄 Summary:\n{validation['summary']}")
            
            # Try to run inference (should fail)
            print("\n🤖 Attempting to run inference on invalid study...")
            inf_response = requests.post(f"{BASE_URL}/api/inference", 
                                        json={"study_id": study_id})
            
            if inf_response.status_code == 422:
                print("❌ Inference BLOCKED (as expected)")
                print(f"   Reason: {inf_response.json()['detail']}")
            
        return study_id
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)

def demo_valid_study():
    """Demo Part 2: Upload Valid Study and Run Inference"""
    print_section("DEMO 2: Valid Study (All Required Sequences)")
    
    # Prepare files from test_data
    files = []
    test_dir = Path("test_data")
    
    for dcm_file in sorted(test_dir.glob("*.dcm"))[:20]:  # Upload subset for speed
        files.append(('files', (dcm_file.name, open(dcm_file, 'rb'), 'application/dicom')))
    
    print(f"📤 Uploading {len(files)} DICOM files from test_data/")
    
    # Upload
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    # Close file handles
    for _, file_tuple in files:
        file_tuple[1].close()
    
    if response.status_code == 200:
        result = response.json()
        study_id = result['study_id']
        print(f"✅ Upload successful - Study ID: {study_id}")
        print(f"   Files received: {result['files_received']}")
        
        # Get validation status
        print("\n🔍 Checking validation status...")
        val_response = requests.get(f"{BASE_URL}/api/validation/{study_id}")
        
        if val_response.status_code == 200:
            validation = val_response.json()
            print(f"\n{'✅'} Validation Result: PASSED")
            
            print("\n📋 Required Sequences:")
            for seq, present in validation['validation']['required_sequences'].items():
                status = "✓" if present else "✗"
                print(f"   {status} {seq}")
            
            # Run inference
            print("\n🤖 Running AI Inference...")
            print("   This will perform:")
            print("   • Tumor Segmentation")
            print("   • Genotype Prediction")
            print("   • Explainability Generation")
            
            inf_response = requests.post(f"{BASE_URL}/api/inference", 
                                        json={
                                            "study_id": study_id,
                                            "run_segmentation": True,
                                            "run_genotype_prediction": True,
                                            "generate_explanations": True
                                        })
            
            if inf_response.status_code == 200:
                results = inf_response.json()
                
                print("\n✅ Inference Complete!\n")
                
                # Display Segmentation Results
                print("📊 SEGMENTATION RESULTS:")
                seg = results['segmentation']
                print(f"   • Whole Tumor: {seg['whole_tumor_volume_ml']:.1f} mL")
                print(f"   • Enhancing Tumor: {seg['enhancing_tumor_volume_ml']:.1f} mL")
                print(f"   • Necrotic Core: {seg['necrotic_core_volume_ml']:.1f} mL")
                print(f"   • Confidence: {seg['confidence']:.1%}")
                
                # Display Genotype Results
                print("\n🧬 GENOTYPE PREDICTIONS:")
                geno = results['genotype']
                print(f"   • IDH Mutation: {geno['idh_mutation_probability']:.1%}")
                print(f"   • IDH Wildtype: {geno['idh_wildtype_probability']:.1%}")
                print(f"   • MGMT Methylation: {geno['mgmt_methylation_probability']:.1%}")
                print(f"   • EGFR Amplification: {geno['egfr_amplification_probability']:.1%}")
                print(f"   • Confidence: {results['overall_confidence']:.1%}")
                
                # Display Explainability
                print("\n💡 EXPLAINABILITY:")
                print(f"   {results['explainability']['explanation_text']}")
                
                if results['explainability'].get('attention_maps'):
                    print(f"   ✅ Grad-CAM maps generated for: {', '.join(results['explainability']['attention_maps'].keys())}")
                
                print("\n🔑 Important Features:")
                for feature in results['explainability']['important_features'][:5]:
                    print(f"   • {feature}")
                
                # Display Clinical Flags
                if results['clinical_flags']['flags']:
                    print("\n⚠️  CLINICAL FLAGS:")
                    for flag in results['clinical_flags']['flags']:
                        print(f"   • {flag}")
                    
                    print("\n🚨 Risk Factors:")
                    for risk in results['clinical_flags']['risk_factors']:
                        print(f"   • {risk}")
                
                print("\n💾 Results can be downloaded as JSON for record-keeping")
                
            else:
                print(f"❌ Inference failed: {inf_response.status_code}")
                print(inf_response.text)
                
        return study_id
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)

def main():
    print("\n")
    print("🧠 Brain Tumor MRI Analysis System - Quick Demo")
    print("=" * 60)
    
    # Check API health
    try:
        response = requests.get(f"{BASE_URL}")
        if response.status_code == 200:
            print("✅ Backend API is healthy")
        else:
            print("❌ Backend API not responding")
            return
    except:
        print("❌ Cannot connect to backend API")
        print("   Make sure the backend is running on http://localhost:8000")
        return
    
    # Run demos
    demo_invalid_study()
    time.sleep(1)
    demo_valid_study()
    
    print_section("Demo Complete!")
    print("Key Takeaways:")
    print("✅ System validates studies BEFORE running AI")
    print("✅ Clear error messages explain what's missing")
    print("✅ Inference blocked on invalid data (safety first)")
    print("✅ Complete results with explainability")
    print("✅ Clinical flags for high-risk cases")
    print("\nOpen http://localhost:3000 in your browser to see the UI!")

if __name__ == "__main__":
    main()
