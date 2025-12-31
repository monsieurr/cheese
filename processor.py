import os
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
INPUT_DIR = "raw_photos"
OUTPUT_DIR = "ready_to_post"
FONT_PATH = "fonts/Roboto-Bold.ttf" # Put a .ttf file in this folder!
YEAR = 2025

# Design Config
BORDER_WIDTH_RATIO = 0.15  # The white bar will be 15% of the image width
TEXT_COLOR = (0, 0, 0)     # Black text
BG_COLOR = (255, 255, 255) # White background
# ---------------------

def get_day_suffix(n):
    """Returns 'st', 'nd', 'rd', or 'th' for a day number."""
    if 11 <= (n % 100) <= 13: suffix = 'th'
    else: suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def process_image(filename):
    """
    Reads an image, expects filename format like '2025-01-01.jpg'
    or simply maps sorted files to days if you prefer.
    Here we assume the filename IS the target date.
    """
    try:
        # Parse date from filename "2025-01-01.jpg"
        date_str = os.path.splitext(filename)[0]
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        # Calculate Day Number (Day of Year)
        day_of_year = date_obj.timetuple().tm_yday
        day_text = f"#{day_of_year:03d}" # e.g. #001
        
        # Format Date Text (e.g. "01 JAN")
        date_display = date_obj.strftime("%d %b").upper()
        
    except ValueError:
        print(f"Skipping {filename}: Filename must be YYYY-MM-DD.jpg")
        return

    img_path = os.path.join(INPUT_DIR, filename)
    with Image.open(img_path) as img:
        # 1. Resize/Crop Logic (Optional: enforce aspect ratio here if needed)
        # For now, we keep original aspect ratio but ensure it's not massive
        # Max width 1080 is standard for IG
        base_width = 1080
        w_percent = (base_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)

        # 2. Create the Canvas (Image + Right Border)
        border_width = int(img.width * BORDER_WIDTH_RATIO)
        total_width = img.width + border_width
        total_height = img.height
        
        new_img = Image.new("RGB", (total_width, total_height), BG_COLOR)
        new_img.paste(img, (0, 0))

        # 3. Add Vertical Text
        # We draw text on a separate transparent layer, rotate it, and paste it back
        txt_layer = Image.new("RGBA", (border_width, total_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Load Font (Dynamic size based on border width)
        font_size = int(border_width * 0.4)
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except OSError:
            print("Font file not found. Using default.")
            font = ImageFont.load_default()

        # Calculate text positions (Bottom aligned)
        # We write horizontally first, then rotate the whole strip
        
        # Let's actually create a horizontal strip the size of the border height
        # write on it, then rotate 90 degrees counter-clockwise
        
        strip_w = total_height
        strip_h = border_width
        strip_img = Image.new("RGBA", (strip_w, strip_h), (255, 255, 255, 0))
        s_draw = ImageDraw.Draw(strip_img)
        
        # Text 1: Day Number (Far Right in horizontal -> Top in vertical)
        s_draw.text((strip_w - 50, strip_h//2), day_text, font=font, fill=TEXT_COLOR, anchor="rm")
        
        # Text 2: Date (A bit before that)
        s_draw.text((strip_w - 250, strip_h//2), date_display, font=font, fill=TEXT_COLOR, anchor="rm")

        # Rotate the strip 270 degrees (or -90) to make it vertical on the right
        rotated_strip = strip_img.rotate(270, expand=True)
        
        # The rotated strip might have different dimensions, center it in the border area
        # Actually, simply pasting the rotated strip into the text layer
        # Coordinates for right border: (img.width, 0)
        
        new_img.paste(rotated_strip, (img.width, 0), rotated_strip)

        # 4. Save
        output_path = os.path.join(OUTPUT_DIR, filename)
        new_img.save(output_path, quality=95)
        print(f"Processed: {output_path}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.jpg', '.jpeg'))]
    if not files:
        print(f"No JPG files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} images. Processing...")
    for f in files:
        process_image(f)
    print("Batch processing complete.")

if __name__ == "__main__":
    main()