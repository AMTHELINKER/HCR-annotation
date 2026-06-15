import os
import sys
from PIL import Image
from tqdm import tqdm

# Add backend to path so we can import from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.services.detection_service import detect_lines, parse_response, filter_predictions
from backend.services.image_service import crop_prediction

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(base_dir, "dataset", "images")
    crops_dir = os.path.join(base_dir, "dataset", "crops")
    
    # Create the crops directory if it doesn't exist
    os.makedirs(crops_dir, exist_ok=True)
    
    # Get all image files
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = [f for f in os.listdir(images_dir) if os.path.splitext(f)[1].lower() in valid_extensions]
    
    print(f"Found {len(image_files)} images to process.")
    
    for filename in tqdm(image_files, desc="Cropping medicines"):
        filepath = os.path.join(images_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        try:
            # Open the image
            img = Image.open(filepath).convert("RGB")
            
            # Detect lines
            result = detect_lines(img, use_cache=True)
            
            # Parse and filter predictions
            parsed = parse_response(result)
            # Default confidence 0.4 and target class "medicament"
            predictions = filter_predictions(parsed["predictions"], 0.4, target_class="medicament")
            
            if not predictions:
                print(f"No medicines found in {filename}")
                continue
                
            # Crop and save each prediction
            for i, pred in enumerate(predictions):
                crop_img = crop_prediction(img, pred)
                crop_filename = f"{base_name}_{i+1}.jpeg"
                crop_filepath = os.path.join(crops_dir, crop_filename)
                
                crop_img.save(crop_filepath, "JPEG", quality=95)
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()
