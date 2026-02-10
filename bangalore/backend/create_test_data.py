"""
Script to create mock DICOM test files for testing the MRI analysis system.
"""
import pydicom
from pydicom.dataset import Dataset, FileDataset
import numpy as np
from datetime import datetime
import os


def create_mock_dicom(filename, series_desc, series_uid, series_number, num_slices=15, modality="MR"):
    """
    Create mock DICOM files for a series
    
    Args:
        filename: Base filename (will be appended with slice number)
        series_desc: Series description
        series_uid: Series UID
        series_number: Series number
        num_slices: Number of slices to create
        modality: DICOM modality
    """
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    
    for slice_num in range(1, num_slices + 1):
        file_meta = Dataset()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
        file_meta.MediaStorageSOPInstanceUID = f"{series_uid}.{slice_num}"
        file_meta.ImplementationClassUID = "1.2.3.4.5"
        
        # Create the dataset
        base_name = filename.replace('.dcm', '')
        slice_filename = f"{base_name}_{slice_num:03d}.dcm"
        
        ds = FileDataset(slice_filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
        
        # Patient/Study information
        ds.PatientName = "TEST^PATIENT"
        ds.PatientID = "TEST001"
        ds.PatientBirthDate = '19800101'
        ds.PatientSex = 'M'
        
        # Study information
        ds.StudyInstanceUID = "1.2.840.99999.12345.67890"
        ds.StudyDate = datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.now().strftime('%H%M%S')
        ds.StudyDescription = "Brain MRI with contrast"
        ds.AccessionNumber = "ACC001"
        
        # Series information
        ds.SeriesInstanceUID = series_uid
        ds.SeriesNumber = series_number
        ds.SeriesDescription = series_desc
        ds.Modality = modality
        
        # Instance information
        ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.4'
        ds.SOPInstanceUID = f"{series_uid}.{slice_num}"
        ds.InstanceNumber = slice_num
        
        # Image information
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows = 256
        ds.Columns = 256
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        ds.PixelSpacing = [1.0, 1.0]
        ds.SliceThickness = 5.0
        ds.ImagePositionPatient = [0, 0, slice_num * 5.0]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        
        # Create mock pixel data (random noise)
        pixel_array = np.random.randint(0, 4096, (256, 256), dtype=np.uint16)
        # Add a bright spot in the center for some slices (simulated tumor)
        if 5 <= slice_num <= 10:
            center = 128
            size = 30
            pixel_array[center-size:center+size, center-size:center+size] = np.random.randint(3000, 4096, (size*2, size*2))
        
        ds.PixelData = pixel_array.tobytes()
        
        # Save the file
        ds.save_as(slice_filename, write_like_original=False)
        print(f"Created {slice_filename}")
    
    print(f"✓ Created {num_slices} slices for {series_desc}")


def create_complete_study(output_dir="test_data"):
    """
    Create a complete valid MRI study with all required sequences
    """
    print("Creating complete MRI study...")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create T1 sequence
    create_mock_dicom(
        os.path.join(output_dir, "t1.dcm"),
        "T1-weighted axial",
        "1.2.840.99999.100",
        100,
        num_slices=20
    )
    
    # Create T1c sequence (T1 with contrast)
    create_mock_dicom(
        os.path.join(output_dir, "t1c.dcm"),
        "T1-weighted axial post contrast",
        "1.2.840.99999.200",
        200,
        num_slices=20
    )
    
    # Create T2 sequence
    create_mock_dicom(
        os.path.join(output_dir, "t2.dcm"),
        "T2-weighted axial",
        "1.2.840.99999.300",
        300,
        num_slices=20
    )
    
    # Create FLAIR sequence
    create_mock_dicom(
        os.path.join(output_dir, "flair.dcm"),
        "FLAIR axial",
        "1.2.840.99999.400",
        400,
        num_slices=20
    )
    
    print("=" * 60)
    print(f"✓ Complete study created in '{output_dir}' directory")
    print(f"  Total files: ~80 DICOM files (20 slices × 4 sequences)")
    print(f"\nThis study will PASS validation (all required sequences present)")


def create_incomplete_study(output_dir="test_data_invalid"):
    """
    Create an incomplete MRI study (missing T1c) - will FAIL validation
    """
    print("Creating incomplete MRI study (missing T1c)...")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create T1 sequence
    create_mock_dicom(
        os.path.join(output_dir, "t1.dcm"),
        "T1-weighted axial",
        "1.2.840.99999.100",
        100,
        num_slices=20
    )
    
    # Create T2 sequence
    create_mock_dicom(
        os.path.join(output_dir, "t2.dcm"),
        "T2-weighted axial",
        "1.2.840.99999.300",
        300,
        num_slices=20
    )
    
    # Create FLAIR sequence
    create_mock_dicom(
        os.path.join(output_dir, "flair.dcm"),
        "FLAIR axial",
        "1.2.840.99999.400",
        400,
        num_slices=20
    )
    
    print("=" * 60)
    print(f"✓ Incomplete study created in '{output_dir}' directory")
    print(f"  Missing: T1c (T1 with contrast)")
    print(f"\nThis study will FAIL validation - Use to test rejection!")


if __name__ == "__main__":
    print("\n🏥 DICOM Test Data Generator")
    print("=" * 60)
    print()
    
    # Create valid study
    create_complete_study("test_data")
    print()
    
    # Create invalid study
    create_incomplete_study("test_data_invalid")
    print()
    
    print("=" * 60)
    print("✓ Test data generation complete!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Start the frontend: cd frontend && npm run dev")
    print("3. Upload 'test_data' folder (should PASS validation)")
    print("4. Upload 'test_data_invalid' folder (should FAIL validation)")
