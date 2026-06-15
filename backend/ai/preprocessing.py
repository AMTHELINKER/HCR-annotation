# =============================================================
# Prétraitement — Préparation des images avant inférence HTR
# =============================================================
# Toute transformation appliquée à l'image AVANT qu'elle soit
# envoyée au modèle. Permet d'améliorer la qualité de la
# transcription sans modifier le modèle.
# =============================================================

from PIL import Image, ImageEnhance, ImageFilter


def to_rgb(image: Image.Image) -> Image.Image:
    """Convertit en RGB si nécessaire (RGBA, L, P, etc.)."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Augmente le contraste pour améliorer la lisibilité.
    
    Args:
        factor: 1.0 = original, >1.0 = plus de contraste.
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def enhance_sharpness(image: Image.Image, factor: float = 1.3) -> Image.Image:
    """Augmente la netteté pour les textes flous.
    
    Args:
        factor: 1.0 = original, >1.0 = plus net.
    """
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def denoise(image: Image.Image) -> Image.Image:
    """Applique un filtre médian léger pour réduire le bruit."""
    return image.filter(ImageFilter.MedianFilter(size=3))


def normalize_size(image: Image.Image, max_width: int = 800,
                    max_height: int = 100) -> Image.Image:
    """Redimensionne l'image si elle dépasse les dimensions maximales.
    
    Conserve le ratio d'aspect. Utile pour normaliser les crops
    de lignes de tailles très variables.
    """
    w, h = image.size
    if w <= max_width and h <= max_height:
        return image

    ratio = min(max_width / w, max_height / h)
    new_size = (int(w * ratio), int(h * ratio))
    return image.resize(new_size, Image.LANCZOS)


def pad_to_square(image: Image.Image, color: tuple = (255, 255, 255)) -> Image.Image:
    """Ajoute du padding pour obtenir une image carrée (utile pour certains modèles)."""
    w, h = image.size
    size = max(w, h)
    padded = Image.new("RGB", (size, size), color)
    padded.paste(image, ((size - w) // 2, (size - h) // 2))
    return padded


def prepare_for_htr(image: Image.Image, enhance: bool = True) -> Image.Image:
    """Pipeline complet de prétraitement avant HTR.
    
    Enchaîne les transformations dans l'ordre optimal :
        1. Conversion RGB
        2. Normalisation de taille
        3. Amélioration contraste (optionnel)
        4. Amélioration netteté (optionnel)
    
    Args:
        image: Image PIL brute (crop de ligne d'ordonnance).
        enhance: Activer les améliorations visuelles.
    
    Returns:
        Image PIL prête pour l'inférence du modèle HTR.
    """
    image = to_rgb(image)
    image = normalize_size(image)

    if enhance:
        image = enhance_contrast(image, factor=1.3)
        image = enhance_sharpness(image, factor=1.2)

    return image
