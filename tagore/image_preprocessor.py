"""
Image Preprocessing Pipeline - Strategy 2
Adaptive image enhancement for historical document OCR
"""

import cv2
import numpy as np
from PIL import Image
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional
from skimage import filters, morphology, exposure
from skimage.transform import rotate
from scipy.ndimage import interpolation as inter

from tagore_config import PREPROCESSING_CONFIG


class ImagePreprocessor:
    """
    Comprehensive image preprocessing pipeline for historical documents.
    Implements Strategy 2: Adaptive Image Pre-processing Pipeline
    """

    def __init__(self, config: Dict = None):
        """
        Initialize preprocessor with configuration.

        Args:
            config: Preprocessing configuration (defaults to PREPROCESSING_CONFIG)
        """
        self.config = config or PREPROCESSING_CONFIG
        self.logger = logging.getLogger(__name__)

    def preprocess(self, image_path: Path, output_dir: Path = None) -> Dict[str, Path]:
        """
        Run full preprocessing pipeline on image.

        Args:
            image_path: Path to input image
            output_dir: Directory to save processed versions

        Returns:
            Dictionary mapping preprocessing variant names to file paths
        """
        self.logger.info(f"Preprocessing image: {image_path.name}")

        # Load image
        image = self._load_image(image_path)
        original = image.copy()

        results = {}

        # Step 1: Deskewing
        if self.config['deskew_enabled']:
            image = self._deskew(image)
            self.logger.debug("Applied deskewing")

        # Step 2: Denoise (optional - preserve original too)
        if self.config['denoise_enabled']:
            denoised = self._denoise(image)
            image = denoised
            self.logger.debug("Applied denoising")

        # Step 3: Binarization (try multiple methods)
        binary_images = self._binarize_multiple(image)

        # Step 4: Select best binarization
        best_binary = self._select_best_binarization(binary_images, image)

        # Step 5: Contrast enhancement (on grayscale, before binarization)
        enhanced = self._enhance_contrast(image)

        # Step 6: Border removal
        if self.config['remove_borders']:
            best_binary = self._remove_borders(best_binary)
            enhanced = self._remove_borders(enhanced)
            self.logger.debug("Removed borders")

        # Save variants if output directory provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            stem = image_path.stem

            # Save different variants for different OCR engines
            results['original'] = image_path
            results['binary_otsu'] = self._save_image(
                binary_images.get('otsu'), output_dir / f"{stem}_binary_otsu.png"
            )
            results['binary_sauvola'] = self._save_image(
                binary_images.get('sauvola'), output_dir / f"{stem}_binary_sauvola.png"
            )
            results['binary_best'] = self._save_image(
                best_binary, output_dir / f"{stem}_binary_best.png"
            )
            results['enhanced'] = self._save_image(
                enhanced, output_dir / f"{stem}_enhanced.png"
            )
            results['grayscale'] = self._save_image(
                image, output_dir / f"{stem}_grayscale.png"
            )

            self.logger.info(f"Saved {len(results)} preprocessed variants")

        return results

    def _load_image(self, image_path: Path) -> np.ndarray:
        """Load image and convert to grayscale."""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        return img

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct page rotation/skew.
        Uses Hough transform to detect dominant angle.
        """
        # Threshold image
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Detect edges
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            self.logger.warning("No lines detected for deskewing")
            return image

        # Calculate angles
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = (theta * 180 / np.pi) - 90
            angles.append(angle)

        # Get median angle
        median_angle = np.median(angles)

        # Only deskew if angle is significant
        if abs(median_angle) > self.config['deskew_angle_threshold']:
            # Rotate image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)
            self.logger.debug(f"Deskewed by {median_angle:.2f} degrees")
            return rotated

        return image

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise while preserving text edges.
        Uses bilateral filter and morphological operations.
        """
        # Bilateral filter (preserves edges)
        denoised = cv2.bilateralFilter(
            image,
            self.config['bilateral_filter_d'],
            self.config['bilateral_filter_sigma_color'],
            self.config['bilateral_filter_sigma_space']
        )

        # Morphological operations
        kernel = np.ones(self.config['denoise_kernel_size'], np.uint8)
        denoised = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel)

        return denoised

    def _binarize_multiple(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Apply multiple binarization methods and return all results.
        """
        results = {}

        methods = self.config['binarization_methods']

        if 'otsu' in methods:
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            results['otsu'] = binary

        if 'sauvola' in methods:
            # Sauvola's method (local adaptive)
            window_size = self.config['sauvola_window_size']
            k = self.config['sauvola_k']
            binary = self._sauvola_threshold(image, window_size, k)
            results['sauvola'] = binary

        if 'wolf' in methods:
            # Wolf's method (for very degraded documents)
            binary = self._wolf_threshold(image)
            results['wolf'] = binary

        if 'adaptive' in methods:
            # OpenCV adaptive threshold
            binary = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            results['adaptive'] = binary

        return results

    def _sauvola_threshold(self, image: np.ndarray, window_size: int, k: float) -> np.ndarray:
        """
        Sauvola's local adaptive thresholding.
        Better for documents with uneven lighting.
        """
        try:
            from skimage.filters import threshold_sauvola
            thresh_sauvola = threshold_sauvola(image, window_size=window_size, k=k)
            binary = (image > thresh_sauvola).astype(np.uint8) * 255
            return binary
        except ImportError:
            self.logger.warning("Sauvola thresholding requires scikit-image")
            return self._binarize_multiple(image)['otsu']

    def _wolf_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Wolf's method for heavily degraded documents.
        """
        # Simplified Wolf implementation using local statistics
        window_size = 25
        k = 0.5

        # Calculate local mean and std
        mean = cv2.blur(image.astype(float), (window_size, window_size))
        mean_sq = cv2.blur((image.astype(float))**2, (window_size, window_size))
        std = np.sqrt(mean_sq - mean**2)

        # Wolf threshold
        threshold = mean + k * std
        binary = (image > threshold).astype(np.uint8) * 255

        return binary

    def _select_best_binarization(self, binary_images: Dict[str, np.ndarray],
                                  original: np.ndarray) -> np.ndarray:
        """
        Select the best binarization result based on quality metrics.
        """
        if not binary_images:
            return self._binarize_multiple(original)['otsu']

        # Score each binarization
        scores = {}
        for method, binary in binary_images.items():
            # Metrics: contrast, edge preservation, noise level
            score = self._score_binarization(binary, original)
            scores[method] = score
            self.logger.debug(f"Binarization {method} score: {score:.3f}")

        # Select best
        best_method = max(scores, key=scores.get)
        self.logger.info(f"Selected binarization method: {best_method}")

        return binary_images[best_method]

    def _score_binarization(self, binary: np.ndarray, original: np.ndarray) -> float:
        """
        Score a binarization result.
        Higher score = better quality.
        """
        # 1. Contrast (variance of binary regions)
        contrast = np.std(binary)

        # 2. Edge preservation (compare edges with original)
        edges_original = cv2.Canny(original, 50, 150)
        edges_binary = cv2.Canny(binary, 50, 150)
        edge_similarity = np.sum(edges_original & edges_binary) / np.sum(edges_original)

        # 3. Noise level (isolated pixels)
        kernel = np.ones((3, 3), np.uint8)
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        noise_level = 1.0 - (np.sum(binary != opened) / binary.size)

        # Weighted score
        score = (0.3 * contrast/255) + (0.5 * edge_similarity) + (0.2 * noise_level)

        return score

    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance contrast using CLAHE and gamma correction.
        """
        if not self.config['clahe_enabled']:
            return image

        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(
            clipLimit=self.config['clahe_clip_limit'],
            tileGridSize=self.config['clahe_tile_grid_size']
        )
        enhanced = clahe.apply(image)

        # Gamma correction for faded text
        gamma = self.config['gamma_correction']
        if gamma != 1.0:
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255
                            for i in range(256)]).astype("uint8")
            enhanced = cv2.LUT(enhanced, table)

        return enhanced

    def _remove_borders(self, image: np.ndarray) -> np.ndarray:
        """
        Remove scanning artifacts and borders.
        """
        # Find content bounding box
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return image

        # Get bounding box of largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Add small margin
        margin = int(min(w, h) * self.config['border_threshold'])
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(image.shape[1] - x, w + 2*margin)
        h = min(image.shape[0] - y, h + 2*margin)

        # Crop
        cropped = image[y:y+h, x:x+w]

        return cropped

    def _save_image(self, image: Optional[np.ndarray], path: Path) -> Optional[Path]:
        """Save image to file."""
        if image is None:
            return None

        try:
            cv2.imwrite(str(path), image)
            return path
        except Exception as e:
            self.logger.error(f"Failed to save image {path}: {e}")
            return None


if __name__ == '__main__':
    # Test preprocessing
    logging.basicConfig(level=logging.DEBUG)

    preprocessor = ImagePreprocessor()

    # Example usage:
    # results = preprocessor.preprocess(
    #     Path("data/images/page001.jpg"),
    #     Path("data/processed")
    # )
    # print(f"Generated {len(results)} preprocessed variants")
