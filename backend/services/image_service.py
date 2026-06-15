# =============================================================
# Service Image — Découpe, annotation et traitement visuel
# =============================================================

from PIL import Image, ImageDraw, ImageFont

# Palette de couleurs pour les bounding boxes
BOX_COLORS = [
    (99, 102, 241),   # Indigo
    (16, 185, 129),   # Emerald
    (239, 68, 68),    # Red
    (245, 158, 11),   # Amber
    (6, 182, 212),    # Cyan
    (236, 72, 153),   # Pink
]


def crop_prediction(image: Image.Image, prediction: dict, padding: int = 6) -> Image.Image:
    """Découpe une zone de prédiction de l'image avec marge.
    
    Args:
        image: Image source PIL.
        prediction: Dict Roboflow {x, y, width, height, ...}.
        padding: Marge en pixels autour de la zone.
    
    Returns:
        Image PIL découpée.
    """
    w_img, h_img = image.size
    x, y = prediction.get("x", 0), prediction.get("y", 0)
    w, h = prediction.get("width", 0), prediction.get("height", 0)

    xmin = max(0, int(x - w / 2 - padding))
    ymin = max(0, int(y - h / 2 - padding))
    xmax = min(w_img, int(x + w / 2 + padding))
    ymax = min(h_img, int(y + h / 2 + padding))

    return image.crop((xmin, ymin, xmax, ymax))


def draw_predictions(image: Image.Image, predictions: list,
                      min_confidence: float = 0.3) -> tuple[Image.Image, int]:
    """Dessine les bounding boxes annotées sur l'image.
    
    Returns:
        (image_annotée, nombre_de_détections)
    """
    img = image.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    width, height = img.size

    # Charger une police
    font = None
    for font_name in ("LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(font_name, max(14, int(height * 0.02)))
            break
        except IOError:
            continue
    if font is None:
        font = ImageFont.load_default()

    class_colors = {}
    color_idx = 0
    draw_count = 0

    for pred in predictions:
        conf = pred.get("confidence", 0.0)
        if conf < min_confidence:
            continue

        draw_count += 1
        cls = pred.get("class", "object")
        if cls not in class_colors:
            class_colors[cls] = BOX_COLORS[color_idx % len(BOX_COLORS)]
            color_idx += 1
        color = class_colors[cls]

        x, y = pred.get("x", 0), pred.get("y", 0)
        w, h = pred.get("width", 0), pred.get("height", 0)
        xmin = max(0, int(x - w / 2))
        ymin = max(0, int(y - h / 2))
        xmax = min(width, int(x + w / 2))
        ymax = min(height, int(y + h / 2))

        # Boîte avec remplissage semi-transparent
        draw.rectangle([xmin, ymin, xmax, ymax], fill=(*color, 25), outline=(*color, 200), width=3)
        draw.rectangle([xmin - 1, ymin - 1, xmax + 1, ymax + 1], fill=None, outline=(*color, 80), width=1)

        # Étiquette
        label = f"{cls} {conf:.1%}"
        try:
            bbox = draw.textbbox((xmin, ymin), label, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(label, font=font)

        ly = max(0, ymin - th - 10)
        lx = min(width, xmin + tw + 16)
        draw.rectangle([xmin, ly, lx, ymin], fill=(*color, 230))
        draw.text((xmin + 8, ly + 4), label, fill=(255, 255, 255, 255), font=font)

    return img, draw_count
