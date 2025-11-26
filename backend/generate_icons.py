from PIL import Image, ImageDraw, ImageFont
import os
import math

def create_gradient(width, height, start_color, end_color):
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            # Calculate distance from top-left
            p = (x + y) / (width + height)
            mask_data.append(int(255 * p))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def generate_icon(size, output_path):
    # Colors from Logo.tsx (approximate hex values for Tailwind colors)
    # purple-500: #a855f7
    # pink-500: #ec4899
    # orange-400: #fb923c
    
    # Create background with gradient
    # We'll simplified gradient from purple to orange/pink
    img = create_gradient(size, size, (168, 85, 247), (251, 146, 60))
    
    # Draw a circle mask to make it round (optional for PWA icons which can be square, 
    # but Android often masks them. Let's keep it square with rounded corners or just fill the square 
    # effectively since the manifest usually expects a square that gets masked by the OS)
    # Actually, PWA icons should usually be square (no transparency) for best results on all platforms,
    # or have a safe zone. Let's make it a filled square with the gradient.
    
    draw = ImageDraw.Draw(img)
    
    # Draw the "P"
    # Try to load a font, fallback to default
    try:
        # MacOS path
        font_path = "/System/Library/Fonts/HelveticaNeue.ttc"
        if not os.path.exists(font_path):
             font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        
        font_size = int(size * 0.6)
        font = ImageFont.truetype(font_path, font_size, index=0)
    except Exception:
        font = ImageFont.load_default()
    
    text = "P"
    
    # Get text bbox to center it
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    x = (size - text_width) / 2 - left
    y = (size - text_height) / 2 - top
    
    # Draw text with shadow
    shadow_offset = int(size * 0.02)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 50))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    img.save(output_path)
    print(f"Generated {output_path}")

def main():
    public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'public')
    
    generate_icon(192, os.path.join(public_dir, 'pwa-192x192.png'))
    generate_icon(512, os.path.join(public_dir, 'pwa-512x512.png'))

    # Also generate favicon and apple-touch-icon if they don't exist or just overwrite to match
    generate_icon(64, os.path.join(public_dir, 'favicon.ico'))
    generate_icon(180, os.path.join(public_dir, 'apple-touch-icon.png'))

if __name__ == "__main__":
    main()