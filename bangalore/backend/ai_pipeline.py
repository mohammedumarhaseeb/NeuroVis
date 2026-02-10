"""
AI Pipeline for tumor segmentation and genotype prediction.
Runs ONLY on validated studies.
"""
import logging
import numpy as np
import time
from typing import Optional, Tuple
import base64
from io import BytesIO
from PIL import Image

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.ndimage import gaussian_filter, label
from scipy import stats

from schemas import (
    DicomStudy, TumorSegmentation, GenotypeIPrediction, 
    ExplainabilityData, ClinicalFlags, MRISequenceType
)

# Optional dependencies for advanced explainability
try:
    import torch
    import monai
    from monai.visualize import GradCAM
    import cv2
    HAS_ADVANCED_AI = True
except ImportError:
    HAS_ADVANCED_AI = False
    logger.warning("Advanced AI dependencies (torch, monai, cv2) not found. Falling back to simulated explainability.")

logger = logging.getLogger(__name__)


class MockAIModel:
    """
    Mock AI model for demonstration purposes.
    In production, replace with actual pretrained models (e.g., nnU-Net, DeepMedic).
    """
    
    def __init__(self):
        logger.info("MockAIModel initialized (DEMO MODE)")
        logger.warning("Using MOCK AI models - replace with real models for production")
    
    def segment_tumor(self, study: DicomStudy) -> Tuple[np.ndarray, float]:
        """
        Mock tumor segmentation that reads actual DICOM pixel data
        to create realistic brain-shaped visualization with tumor overlay.
        
        Returns:
            Tuple of (segmentation_map, confidence_score)
        """
        import pydicom
        
        time.sleep(0.5)
        
        size = 256
        brain_image = None
        
        # Try to read actual DICOM pixel data from any series
        for series in study.series:
            if series.file_paths:
                try:
                    dcm = pydicom.dcmread(series.file_paths[0], force=True)
                    if hasattr(dcm, 'pixel_array'):
                        raw = dcm.pixel_array.astype(np.float32)
                        # Normalize to 0-255
                        if raw.max() > raw.min():
                            raw = (raw - raw.min()) / (raw.max() - raw.min()) * 255
                        brain_image = np.array(Image.fromarray(raw.astype(np.uint8)).resize((size, size)))
                        logger.info(f"Read DICOM pixel data from {series.file_paths[0]}")
                        break
                except Exception as e:
                    logger.warning(f"Could not read pixel data: {e}")
        
        # If no DICOM data, create synthetic brain phantom
        if brain_image is None:
            brain_image = self._create_brain_phantom(size)
        
        # Store for later use in heatmap generation
        self._last_brain_image = brain_image
        
        # Create realistic tumor segmentation based on brain image
        seg_map = self._create_realistic_segmentation(brain_image, size)
        
        confidence = np.random.uniform(0.82, 0.95)
        logger.debug(f"Segmentation completed with confidence {confidence:.3f}")
        return seg_map, confidence
    
    def _create_brain_phantom(self, size: int) -> np.ndarray:
        """Create a synthetic brain-like image"""
        y, x = np.ogrid[-size//2:size//2, -size//2:size//2]
        
        # Elliptical brain shape
        brain_mask = (x**2 / (size*0.38)**2 + y**2 / (size*0.42)**2) < 1
        
        # Add internal structure
        img = np.zeros((size, size), dtype=np.float32)
        img[brain_mask] = 120
        
        # White matter (inner ellipse)
        wm_mask = (x**2 / (size*0.28)**2 + y**2 / (size*0.32)**2) < 1
        img[wm_mask] = 180
        
        # Ventricles
        vent_mask = (x**2 / (size*0.06)**2 + y**2 / (size*0.15)**2) < 1
        img[vent_mask] = 40
        
        # Add noise for realism
        noise = np.random.normal(0, 8, (size, size))
        img = np.clip(img + noise, 0, 255)
        img[~brain_mask] = 0
        
        return img.astype(np.uint8)
    
    def _create_realistic_segmentation(self, brain_image: np.ndarray, size: int) -> np.ndarray:
        """Create a realistic localized tumor segmentation on the brain"""
        seg_map = np.zeros((size, size), dtype=np.uint8)
        
        # Find brain region (non-zero area)
        brain_mask = brain_image > 20
        
        if not brain_mask.any():
            # Fallback - create centered tumor
            brain_mask = np.ones((size, size), dtype=bool)
        
        # Find valid brain coordinates for tumor center
        brain_coords = np.where(brain_mask)
        if len(brain_coords[0]) == 0:
            return seg_map
        
        # Place tumor in a realistic location (slightly off-center)
        center_y = int(np.mean(brain_coords[0]) + np.random.randint(-size//8, size//8))
        center_x = int(np.mean(brain_coords[1]) + np.random.randint(-size//6, size//6))
        
        # Clamp to valid range
        center_y = max(size//6, min(size - size//6, center_y))
        center_x = max(size//6, min(size - size//6, center_x))
        
        y, x = np.ogrid[:size, :size]
        
        # Tumor core (necrotic) - small irregular center
        tumor_radius = np.random.randint(size//12, size//8)
        core_radius = tumor_radius // 2
        
        # Create irregular shapes using multiple overlapping ellipses
        dist_core = np.sqrt(((y - center_y) / 1.2)**2 + ((x - center_x) * 1.1)**2)
        core_mask = dist_core < core_radius
        core_mask &= brain_mask
        seg_map[core_mask] = 1  # Necrotic
        
        # Enhancing tumor ring around core
        enhance_radius = core_radius + np.random.randint(5, 12)
        enhance_mask = (dist_core >= core_radius) & (dist_core < enhance_radius)
        # Add irregularity
        noise = gaussian_filter(np.random.randn(size, size), sigma=5) * 6
        enhance_mask_noisy = (dist_core + noise >= core_radius) & (dist_core + noise < enhance_radius + 3)
        enhance_mask = enhance_mask | enhance_mask_noisy
        enhance_mask &= brain_mask
        enhance_mask &= ~core_mask
        seg_map[enhance_mask] = 3  # Enhancing
        
        # Edema - larger area surrounding tumor
        edema_radius = tumor_radius + np.random.randint(15, 25)
        edema_noise = gaussian_filter(np.random.randn(size, size), sigma=8) * 10
        edema_mask = (dist_core + edema_noise) < edema_radius
        edema_mask &= brain_mask
        edema_mask &= (seg_map == 0)  # Only where nothing else is
        seg_map[edema_mask] = 2  # Edema
        
        return seg_map
    
    def predict_genotype(self, study: DicomStudy, segmentation: Optional[np.ndarray] = None) -> dict:
        """
        Mock genotype prediction
        
        Returns:
            Dictionary with probabilities
        """
        # Simulate processing time
        time.sleep(0.3)
        
        # Mock probabilities (should sum to reasonable values)
        idh_mut = np.random.uniform(0.3, 0.7)
        idh_wt = 1.0 - idh_mut
        mgmt = np.random.uniform(0.4, 0.8)
        egfr = np.random.uniform(0.2, 0.6)
        confidence = np.random.uniform(0.70, 0.90)
        
        logger.debug(f"Mock genotype prediction completed with confidence {confidence:.3f}")
        
        return {
            'idh_mutation': idh_mut,
            'idh_wildtype': idh_wt,
            'mgmt_methylation': mgmt,
            'egfr_amplification': egfr,
            'confidence': confidence
        }
    
    def generate_attention_maps(self, study: DicomStudy) -> dict:
        """
        Generate Grad-CAM attention maps for study sequences.
        Uses MONAI's GradCAM implementation if dependencies are available.
        """
        attention_maps = {}
        
        # Determine device
        device = "cpu"
        if HAS_ADVANCED_AI:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                # Initialize ResNet-10 (as requested by user)
                model = monai.networks.nets.resnet10(spatial_dims=3, n_input_channels=1, num_classes=1)
                model.to(device)
                model.eval()
                # Initialize Grad-CAM
                cam = GradCAM(nn_module=model, target_layers="layer4")
            except Exception as e:
                logger.error(f"Failed to initialize Grad-CAM model: {e}")
                HAS_ADVANCED_AI_LOCAL = False
            else:
                HAS_ADVANCED_AI_LOCAL = True
        else:
            HAS_ADVANCED_AI_LOCAL = False

        for series in study.series:
            if not series.sequence_type or not series.file_paths:
                continue
                
            seq_type = series.sequence_type
            seq_val = seq_type if isinstance(seq_type, str) else seq_type.value
            
            try:
                # 1. Read the largest/representative slice
                import pydicom
                # Simple heuristic for largest slice: read first one for metadata, or just use the first one
                dcm = pydicom.dcmread(series.file_paths[len(series.file_paths)//2], force=True)
                if not hasattr(dcm, 'pixel_array'):
                    continue
                
                img = dcm.pixel_array.astype(np.float32)
                # Normalize
                if img.max() > img.min():
                    img = (img - img.min()) / (img.max() - img.min())
                
                # 2. Generate Heatmap
                if HAS_ADVANCED_AI_LOCAL:
                    # Prepare 3D input (replicated slice as requested)
                    # We use a depth of 32 for efficiency
                    target_depth = 32
                    img3d = np.repeat(img[:, :, np.newaxis], target_depth, axis=2)
                    # Reshape to [1, 1, H, W, D]
                    tensor_img = torch.tensor(img3d).float().unsqueeze(0).unsqueeze(0).to(device)
                    
                    # Generate CAM
                    with torch.no_grad():
                        result = cam(x=tensor_img)
                    
                    heatmap = result[0, 0].cpu().numpy()
                    heatmap_slice = heatmap[:, :, target_depth // 2]
                else:
                    # Simulated high-quality heatmap based on tumor location
                    # If we have segmentation, we can center it there
                    heatmap_slice = self._simulate_gradcam(img)

                # 3. Process Heatmap (Normalize, Mask, ColorMap)
                # Apply brain mask to suppress non-brain activations
                mask = (img > (img.min() + 0.05 * (img.max() - img.min())))
                heatmap_slice = heatmap_slice * mask
                
                # Normalize
                if heatmap_slice.max() > heatmap_slice.min():
                    heatmap_slice = (heatmap_slice - heatmap_slice.min()) / (heatmap_slice.max() - heatmap_slice.min() + 1e-8)
                
                # 4. Create Overlay
                # Use OpenCV for color mapping if available, otherwise use matplotlib
                if HAS_ADVANCED_AI:
                    heatmap_color = cv2.applyColorMap(np.uint8(255 * heatmap_slice), cv2.COLORMAP_JET)
                    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
                    
                    img_rgb = np.stack([img]*3, axis=-1)
                    overlay = cv2.addWeighted(np.uint8(255 * img_rgb), 0.6, heatmap_color, 0.4, 0)
                    final_img = Image.fromarray(overlay)
                else:
                    # Matplotlib fallback for overlay
                    fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
                    ax.imshow(img, cmap='gray')
                    ax.imshow(heatmap_slice, cmap='jet', alpha=0.4)
                    ax.axis('off')
                    buffered = BytesIO()
                    plt.savefig(buffered, format='PNG', bbox_inches='tight', pad_inches=0)
                    plt.close(fig)
                    final_img = Image.open(buffered)

                # 5. Convert to Base64
                buffered = BytesIO()
                final_img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                attention_maps[seq_val] = img_str
                
            except Exception as e:
                logger.warning(f"Failed to generate Grad-CAM for {seq_val}: {e}")
                # Fallback to random if all fails
                attn = np.random.rand(64, 64)
                attn = (attn * 255).astype(np.uint8)
                img_pil = Image.fromarray(attn, mode='L')
                buffered = BytesIO()
                img_pil.save(buffered, format="PNG")
                attention_maps[seq_val] = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug(f"Generated {len(attention_maps)} Grad-CAM maps")
        return attention_maps

    def _simulate_gradcam(self, img: np.ndarray) -> np.ndarray:
        """Simulate a realistic Grad-CAM heatmap based on image intensities"""
        from scipy.ndimage import gaussian_filter
        # Focus on high intensity areas (where tumors usually are in FLAIR/T2)
        sim = gaussian_filter(img, sigma=8.0)
        # Add some randomness
        noise = gaussian_filter(np.random.rand(*img.shape), sigma=12.0) * 0.3
        sim = sim + noise
        if sim.max() > sim.min():
            sim = (sim - sim.min()) / (sim.max() - sim.min())
        return sim


class TumorSegmentationPipeline:
    """Handles tumor segmentation"""
    
    def __init__(self, model: MockAIModel):
        self.model = model
        logger.info("TumorSegmentationPipeline initialized")
    
    def calculate_volumes(self, segmentation: np.ndarray, voxel_volume_ml: float = 0.008) -> dict:
        """
        Calculate tumor volumes from segmentation map
        
        Args:
            segmentation: Segmentation map (0=background, 1=necrotic, 2=edema, 3=enhancing)
            voxel_volume_ml: Volume of each voxel in mL
            
        Returns:
            Dictionary with volume measurements
        """
        # Count voxels for each label
        necrotic = np.sum(segmentation == 1) * voxel_volume_ml
        edema = np.sum(segmentation == 2) * voxel_volume_ml
        enhancing = np.sum(segmentation == 3) * voxel_volume_ml
        
        whole_tumor = necrotic + edema + enhancing
        
        return {
            'whole_tumor': whole_tumor,
            'enhancing': enhancing,
            'necrotic': necrotic
        }
    
    def encode_segmentation(self, segmentation: np.ndarray) -> str:
        """
        Encode segmentation overlaid on the actual brain MRI image as base64 PNG.
        Shows the real brain with colored tumor regions highlighted on top.
        """
        size = segmentation.shape[0]
        
        # Get the actual brain image
        brain_img = getattr(self.model, '_last_brain_image', None)
        if brain_img is not None:
            brain_rgb = np.stack([brain_img, brain_img, brain_img], axis=-1).astype(np.float32)
            if brain_rgb.shape[0] != size:
                brain_pil = Image.fromarray(brain_rgb.astype(np.uint8)).resize((size, size))
                brain_rgb = np.array(brain_pil).astype(np.float32)
        else:
            brain_rgb = np.ones((size, size, 3), dtype=np.float32) * 30
        
        # Create colored overlay
        overlay = np.zeros((size, size, 3), dtype=np.float32)
        overlay[segmentation == 1] = [255, 60, 60]     # Necrotic - red
        overlay[segmentation == 2] = [60, 220, 80]     # Edema - green
        overlay[segmentation == 3] = [255, 230, 50]    # Enhancing - yellow
        
        # Blend: brain + tumor overlay with alpha
        alpha = 0.45
        result = brain_rgb.copy()
        tumor_mask = segmentation > 0
        result[tumor_mask] = (1 - alpha) * brain_rgb[tumor_mask] + alpha * overlay[tumor_mask]
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        img = Image.fromarray(result, mode='RGB')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
    
    def generate_disease_heatmap(self, segmentation: np.ndarray) -> str:
        """
        Produce a professional disease severity heatmap overlaid on the actual brain MRI.
        Uses a seaborn color palette to show risk from low (green) to critical (red).
        """
        brain_img = getattr(self.model, '_last_brain_image', None)
        
        # Create severity map
        severity = np.zeros(segmentation.shape, dtype=np.float32)
        severity[segmentation == 2] = 0.3   # Edema - low/mod
        severity[segmentation == 3] = 0.7   # Enhancing - high
        severity[segmentation == 1] = 1.0   # Necrotic - critical
        
        severity_smooth = gaussian_filter(severity, sigma=2.5)
        if severity_smooth.max() > 0:
            severity_smooth = severity_smooth / severity_smooth.max()
            
        sns.set_theme(style='dark', rc={
            'figure.facecolor': '#0f172a',
            'axes.facecolor': '#1e293b',
            'text.color': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
        })
        
        fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
        fig.patch.set_facecolor('#0f172a')
        
        # Show brain background
        if brain_img is not None:
            ax.imshow(brain_img, cmap='gray', aspect='equal')
        
        # Overlay severity heatmap
        masked_sev = np.ma.masked_where(severity_smooth < 0.05, severity_smooth)
        im = ax.imshow(masked_sev, cmap='RdYlGn_r', alpha=0.6, aspect='equal', vmin=0, vmax=1)
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.set_ylabel('Disease Severity Index', color='white', fontsize=10)
        cbar.ax.tick_params(colors='#94a3b8')
        
        ax.set_title('Anatomical Severity Heatmap', color='white', fontsize=14, fontweight='bold', pad=15)
        ax.axis('off')
        
        plt.tight_layout()
        
        buffered = BytesIO()
        fig.savefig(buffered, format='PNG', bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug("Generated anatomical disease severity heatmap")
        return img_str
    
    def generate_tumor_density_heatmap(self, segmentation: np.ndarray) -> str:
        """
        Generate tumor density heatmap overlaid on brain MRI using seaborn/matplotlib.
        Shows actual brain with tumor concentration highlighted.
        """
        tumor_mask = (segmentation > 0).astype(np.float32)
        density = gaussian_filter(tumor_mask, sigma=5.0)
        if density.max() > 0:
            density = density / density.max()
        
        sns.set_theme(style='dark', rc={
            'figure.facecolor': '#0f172a',
            'axes.facecolor': '#1e293b',
            'text.color': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
        })
        
        fig, ax = plt.subplots(1, 1, figsize=(6, 6), dpi=120)
        fig.patch.set_facecolor('#0f172a')
        
        # Show brain MRI as background
        brain_img = getattr(self.model, '_last_brain_image', None)
        if brain_img is not None:
            ax.imshow(brain_img, cmap='gray', aspect='equal')
        
        # Overlay density heatmap with transparency
        masked_density = np.ma.masked_where(density < 0.05, density)
        im = ax.imshow(masked_density, cmap='YlOrRd', alpha=0.6, aspect='equal', vmin=0, vmax=1)
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.8, label='Tumor Density')
        cbar.ax.yaxis.label.set_color('white')
        cbar.ax.tick_params(colors='#94a3b8')
        
        ax.set_title('Tumor Density on Brain MRI', fontsize=14, fontweight='bold', color='white', pad=12)
        ax.set_xticks([])
        ax.set_yticks([])
        
        plt.tight_layout()
        
        buffered = BytesIO()
        fig.savefig(buffered, format='PNG', bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug('Generated tumor density heatmap on brain MRI')
        return img_str
    
    def generate_tumor_region_grid(self, segmentation: np.ndarray) -> str:
        """
        Generate a 2x2 grid analysis overlaid on brain MRI using matplotlib.
        Shows: segmentation overlay, density contours, regions, severity zones.
        """
        brain_img = getattr(self.model, '_last_brain_image', None)
        
        sns.set_theme(style='dark', rc={
            'figure.facecolor': '#0f172a',
            'axes.facecolor': '#1e293b',
            'text.color': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
        })
        
        fig, axes = plt.subplots(2, 2, figsize=(10, 9), dpi=120)
        fig.patch.set_facecolor('#0f172a')
        fig.suptitle('Brain Tumor Region Analysis Grid', fontsize=16, fontweight='bold', color='white', y=0.98)
        
        # --- Panel 1: Brain + Segmentation Overlay ---
        ax1 = axes[0, 0]
        if brain_img is not None:
            ax1.imshow(brain_img, cmap='gray', aspect='equal')
        # Overlay colored segmentation
        overlay = np.zeros((*segmentation.shape, 4), dtype=np.float32)
        overlay[segmentation == 1] = [1.0, 0.2, 0.2, 0.5]   # Necrotic - red
        overlay[segmentation == 2] = [0.2, 0.9, 0.3, 0.4]   # Edema - green  
        overlay[segmentation == 3] = [1.0, 0.9, 0.1, 0.5]   # Enhancing - yellow
        ax1.imshow(overlay, aspect='equal')
        ax1.set_title('Tumor Segmentation', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        ax1.set_xticks([]); ax1.set_yticks([])
        
        # --- Panel 2: Brain + Density Contour ---
        ax2 = axes[0, 1]
        if brain_img is not None:
            ax2.imshow(brain_img, cmap='gray', aspect='equal')
        tumor_mask = (segmentation > 0).astype(np.float32)
        density = gaussian_filter(tumor_mask, sigma=4.0)
        if density.max() > 0:
            density = density / density.max()
        masked_density = np.ma.masked_where(density < 0.05, density)
        ax2.imshow(masked_density, cmap='magma', alpha=0.5, aspect='equal')
        ax2.contour(density, levels=5, colors='cyan', linewidths=0.5, alpha=0.7)
        ax2.set_title('Density Contour Map', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        ax2.set_xticks([]); ax2.set_yticks([])
        
        # --- Panel 3: Brain + Labeled Regions ---
        ax3 = axes[1, 0]
        if brain_img is not None:
            ax3.imshow(brain_img, cmap='gray', aspect='equal')
        binary_tumor = (segmentation > 0).astype(np.int32)
        labeled_array, num_features = label(binary_tumor)
        region_overlay = np.zeros((*segmentation.shape, 4), dtype=np.float32)
        region_colors = plt.cm.Set1(np.linspace(0, 1, max(num_features, 1)))
        for i in range(1, num_features + 1):
            region_overlay[labeled_array == i] = [*region_colors[i-1][:3], 0.5]
        ax3.imshow(region_overlay, aspect='equal')
        ax3.set_title(f'Detected Regions ({num_features})', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        ax3.set_xticks([]); ax3.set_yticks([])
        
        # --- Panel 4: Brain + Severity Gradient ---
        ax4 = axes[1, 1]
        if brain_img is not None:
            ax4.imshow(brain_img, cmap='gray', aspect='equal')
        severity = np.zeros(segmentation.shape, dtype=np.float32)
        severity[segmentation == 2] = 0.4
        severity[segmentation == 3] = 0.8
        severity[segmentation == 1] = 1.0
        severity_smooth = gaussian_filter(severity, sigma=2.5)
        if severity_smooth.max() > 0:
            severity_smooth = severity_smooth / severity_smooth.max()
        masked_sev = np.ma.masked_where(severity_smooth < 0.05, severity_smooth)
        im4 = ax4.imshow(masked_sev, cmap='RdYlGn_r', alpha=0.6, aspect='equal', vmin=0, vmax=1)
        fig.colorbar(im4, ax=ax4, shrink=0.7, label='Severity')
        ax4.set_title('Severity Zone Map', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        ax4.set_xticks([]); ax4.set_yticks([])
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        buffered = BytesIO()
        fig.savefig(buffered, format='PNG', bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug('Generated tumor region grid analysis')
        return img_str
    
    def generate_intensity_distribution(self, segmentation: np.ndarray) -> str:
        """
        Generate intensity distribution plot showing tumor type breakdown
        using seaborn and matplotlib.
        """
        sns.set_theme(style='dark', rc={
            'figure.facecolor': '#0f172a',
            'axes.facecolor': '#1e293b',
            'text.color': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
        })
        
        fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), dpi=100)
        fig.patch.set_facecolor('#0f172a')
        fig.suptitle('Tumor Composition Analysis', fontsize=14, fontweight='bold', color='white', y=1.02)
        
        # --- Left: Bar Chart of Tumor Components ---
        ax1 = axes[0]
        labels = ['Necrotic\nCore', 'Edema\n(Swelling)', 'Enhancing\nTumor', 'Healthy\nTissue']
        counts = [
            np.sum(segmentation == 1),
            np.sum(segmentation == 2),
            np.sum(segmentation == 3),
            np.sum(segmentation == 0)
        ]
        total = sum(counts)
        percentages = [(c / total) * 100 if total > 0 else 0 for c in counts]
        
        colors_bar = ['#ef4444', '#22c55e', '#eab308', '#3b82f6']
        bars = ax1.bar(labels, percentages, color=colors_bar, edgecolor='white', linewidth=0.5, width=0.7)
        
        # Add value labels on bars
        for bar, pct in zip(bars, percentages):
            if pct > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                        f'{pct:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold', color='white')
        
        ax1.set_ylabel('Percentage (%)', fontsize=10, color='#94a3b8')
        ax1.set_title('Component Distribution', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color('#334155')
        ax1.spines['bottom'].set_color('#334155')
        
        # --- Right: Pie Chart ---
        ax2 = axes[1]
        tumor_labels = ['Necrotic', 'Edema', 'Enhancing']
        tumor_counts = [np.sum(segmentation == 1), np.sum(segmentation == 2), np.sum(segmentation == 3)]
        tumor_colors = ['#ef4444', '#22c55e', '#eab308']
        
        # Filter out zero values
        filtered = [(l, c, co) for l, c, co in zip(tumor_labels, tumor_counts, tumor_colors) if c > 0]
        
        if filtered:
            f_labels, f_counts, f_colors = zip(*filtered)
            wedges, texts, autotexts = ax2.pie(
                f_counts, labels=f_labels, colors=f_colors, autopct='%1.1f%%',
                startangle=90, textprops={'color': 'white', 'fontsize': 9},
                wedgeprops={'edgecolor': '#0f172a', 'linewidth': 2},
                pctdistance=0.75
            )
            for autotext in autotexts:
                autotext.set_fontweight('bold')
        else:
            ax2.text(0.5, 0.5, 'No tumor\ndetected', transform=ax2.transAxes,
                    ha='center', va='center', fontsize=12, color='#94a3b8')
        
        ax2.set_title('Tumor Type Breakdown', fontsize=11, fontweight='bold', color='#e2e8f0', pad=8)
        
        plt.tight_layout()
        
        # Convert to base64
        buffered = BytesIO()
        fig.savefig(buffered, format='PNG', bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        logger.debug('Generated intensity distribution plot')
        return img_str
    
    def run(self, study: DicomStudy) -> TumorSegmentation:
        """
        Run tumor segmentation pipeline
        
        Args:
            study: Validated DicomStudy
            
        Returns:
            TumorSegmentation result
        """
        logger.info(f"Running tumor segmentation for study {study.study_uid}")
        
        # Run segmentation model
        seg_map, confidence = self.model.segment_tumor(study)
        
        # Calculate volumes
        volumes = self.calculate_volumes(seg_map)
        
        # Encode segmentation for visualization
        seg_encoded = self.encode_segmentation(seg_map)
        
        # Generate disease severity heatmap (PIL-based)
        heatmap_encoded = self.generate_disease_heatmap(seg_map)
        
        # Generate professional visualizations (matplotlib/seaborn/scipy)
        tumor_density = self.generate_tumor_density_heatmap(seg_map)
        tumor_grid = self.generate_tumor_region_grid(seg_map)
        intensity_dist = self.generate_intensity_distribution(seg_map)
        
        result = TumorSegmentation(
            whole_tumor_volume_ml=volumes['whole_tumor'],
            enhancing_tumor_volume_ml=volumes['enhancing'],
            necrotic_core_volume_ml=volumes['necrotic'],
            segmentation_map=seg_encoded,
            disease_heatmap=heatmap_encoded,
            tumor_density_heatmap=tumor_density,
            tumor_region_grid=tumor_grid,
            intensity_distribution=intensity_dist,
            confidence_score=confidence
        )
        
        logger.info(f"Segmentation complete: whole tumor = {volumes['whole_tumor']:.2f} mL")
        return result


class GenotypePredictionPipeline:
    """Handles genotype prediction"""
    
    def __init__(self, model: MockAIModel):
        self.model = model
        logger.info("GenotypePredictionPipeline initialized")
    
    def run(self, study: DicomStudy, segmentation: Optional[np.ndarray] = None) -> GenotypeIPrediction:
        """
        Run genotype prediction pipeline
        
        Args:
            study: Validated DicomStudy
            segmentation: Optional segmentation map for tumor-focused analysis
            
        Returns:
            GenotypeIPrediction result
        """
        logger.info(f"Running genotype prediction for study {study.study_uid}")
        
        # Run prediction model
        predictions = self.model.predict_genotype(study, segmentation)
        
        result = GenotypeIPrediction(
            idh_mutation_probability=predictions['idh_mutation'],
            idh_wildtype_probability=predictions['idh_wildtype'],
            mgmt_methylation_probability=predictions['mgmt_methylation'],
            egfr_amplification_probability=predictions['egfr_amplification'],
            prediction_confidence=predictions['confidence']
        )
        
        logger.info(f"Genotype prediction complete (confidence: {predictions['confidence']:.3f})")
        return result


class ExplainabilityPipeline:
    """Generates explanations and attention maps"""
    
    def __init__(self, model: MockAIModel):
        self.model = model
        logger.info("ExplainabilityPipeline initialized")
    
    def generate_explanation_text(self, 
                                   segmentation: Optional[TumorSegmentation],
                                   genotype: Optional[GenotypeIPrediction]) -> str:
        """
        Generate human-readable explanation
        
        Args:
            segmentation: Segmentation result
            genotype: Genotype prediction result
            
        Returns:
            Explanation text
        """
        explanation_parts = []
        
        if segmentation:
            explanation_parts.append(
                f"Tumor identified with total volume of {segmentation.whole_tumor_volume_ml:.1f} mL. "
                f"Enhancing component: {segmentation.enhancing_tumor_volume_ml:.1f} mL. "
                f"Necrotic core: {segmentation.necrotic_core_volume_ml:.1f} mL."
            )
        
        if genotype:
            # IDH status
            if genotype.idh_mutation_probability > 0.5:
                idh_status = f"IDH-mutant (probability: {genotype.idh_mutation_probability:.1%})"
            else:
                idh_status = f"IDH-wildtype (probability: {genotype.idh_wildtype_probability:.1%})"
            
            # MGMT status
            mgmt_status = "MGMT promoter methylation " + (
                f"likely (probability: {genotype.mgmt_methylation_probability:.1%})" 
                if genotype.mgmt_methylation_probability > 0.5 
                else f"unlikely (probability: {genotype.mgmt_methylation_probability:.1%})"
            )
            
            explanation_parts.append(
                f"Predicted genotype: {idh_status}. {mgmt_status}. "
                f"EGFR amplification probability: {genotype.egfr_amplification_probability:.1%}."
            )
        
        return " ".join(explanation_parts)
    
    def identify_important_features(self, 
                                      segmentation: Optional[TumorSegmentation],
                                      genotype: Optional[GenotypeIPrediction]) -> list:
        """
        Identify important features for the prediction
        
        Returns:
            List of important features
        """
        features = []
        
        if segmentation:
            if segmentation.enhancing_tumor_volume_ml > 10:
                features.append("Large enhancing tumor component")
            if segmentation.necrotic_core_volume_ml > 5:
                features.append("Significant necrotic core")
            features.append("Tumor location in detected region")
        
        if genotype:
            features.append("Signal intensity patterns")
            features.append("T2/FLAIR signal characteristics")
            features.append("Tumor heterogeneity index")
        
        return features
    
    def run(self, 
            study: DicomStudy,
            segmentation: Optional[TumorSegmentation] = None,
            genotype: Optional[GenotypeIPrediction] = None) -> ExplainabilityData:
        """
        Run explainability pipeline
        
        Args:
            study: DicomStudy
            segmentation: Optional segmentation result
            genotype: Optional genotype prediction
            
        Returns:
            ExplainabilityData
        """
        logger.info(f"Generating explanations for study {study.study_uid}")
        
        # Generate attention maps
        attention_maps = self.model.generate_attention_maps(study)
        
        # Generate explanation text
        explanation_text = self.generate_explanation_text(segmentation, genotype)
        
        # Identify important features
        important_features = self.identify_important_features(segmentation, genotype)
        
        result = ExplainabilityData(
            attention_maps=attention_maps,
            important_features=important_features,
            explanation_text=explanation_text
        )
        
        logger.info("Explainability generation complete")
        return result


class ClinicalFlaggingPipeline:
    """Identifies clinical risk factors and urgency flags"""
    
    def __init__(self):
        logger.info("ClinicalFlaggingPipeline initialized")
    
    def run(self, 
            segmentation: Optional[TumorSegmentation],
            genotype: Optional[GenotypeIPrediction]) -> ClinicalFlags:
        """
        Generate clinical flags based on analysis results
        
        Args:
            segmentation: Segmentation result
            genotype: Genotype prediction result
            
        Returns:
            ClinicalFlags
        """
        logger.info("Evaluating clinical risk factors")
        
        risk_factors = []
        high_risk = False
        requires_urgent_review = False
        urgency_reason = None
        
        if segmentation:
            # Large tumor
            if segmentation.whole_tumor_volume_ml > 50:
                risk_factors.append("Large tumor volume (>50 mL)")
                high_risk = True
            
            # Significant enhancement suggests high-grade
            if segmentation.enhancing_tumor_volume_ml > 20:
                risk_factors.append("Significant tumor enhancement")
                high_risk = True
            
            # Large necrotic core
            if segmentation.necrotic_core_volume_ml > 10:
                risk_factors.append("Large necrotic core")
                requires_urgent_review = True
                urgency_reason = "Large necrotic core may indicate high-grade glioma"
        
        if genotype:
            # IDH-wildtype is associated with worse prognosis
            if genotype.idh_wildtype_probability > 0.7:
                risk_factors.append("IDH-wildtype (worse prognosis)")
                high_risk = True
            
            # EGFR amplification
            if genotype.egfr_amplification_probability > 0.6:
                risk_factors.append("EGFR amplification likely")
                high_risk = True
        
        flags = ClinicalFlags(
            high_risk=high_risk,
            requires_urgent_review=requires_urgent_review,
            risk_factors=risk_factors,
            urgency_reason=urgency_reason
        )
        
        if high_risk or requires_urgent_review:
            logger.warning(f"Clinical flags raised: high_risk={high_risk}, urgent={requires_urgent_review}")
        else:
            logger.info("No high-risk flags identified")
        
        return flags
