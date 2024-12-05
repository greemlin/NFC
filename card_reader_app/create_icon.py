from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create directory if it doesn't exist
    if not os.path.exists('images'):
        os.makedirs('images')

    # Create a new image with a white background
    size = 256
    image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Draw a rounded rectangle for the card
    margin = 40
    card_width = size - 2 * margin
    card_height = int(card_width * 0.63)  # Standard card aspect ratio
    top = (size - card_height) // 2

    # Card background
    draw.rounded_rectangle(
        [margin, top, size - margin, top + card_height],
        radius=20,
        fill=(0, 120, 212),  # Blue color
        outline=(0, 90, 180),
        width=3
    )

    # Draw NFC waves
    center_x = size // 2
    center_y = size // 2
    for radius in range(30, 71, 20):
        # Draw partial circles for NFC waves
        draw.arc(
            [center_x - radius, center_y - radius,
             center_x + radius, center_y + radius],
            start=230, end=310,
            fill=(255, 255, 255),
            width=4
        )

    # Save as PNG
    image.save('images/app_icon.png')

    # Save as ICO
    # Convert to RGB mode before saving as ICO
    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
    rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
    rgb_image.save('images/app_icon.ico', format='ICO', sizes=[(256, 256)])

if __name__ == '__main__':
    create_icon()
