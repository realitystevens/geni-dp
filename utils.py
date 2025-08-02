import io
import requests
import cloudinary
import cloudinary.uploader
from decouple import config
from PIL import Image, ImageDraw


cloudinary.config(
    cloud_name=config('CLOUDINARY_CLOUDNAME'),
    api_key=config('CLOUDINARY_APIKEY'),
    api_secret=config('CLOUDINARY_APISECRET'),
    secure=True
)

def is_image_transparent(image: Image.Image) -> bool:
    """
    Checks if the given PIL Image has any fully transparent pixels.
    Returns True if the image is fully transparent, otherwise False.
    """
    if image.mode in ("RGBA", "LA"):
        alpha = image.getchannel("A")
        # Check if all pixels are fully transparent (alpha == 0)
        return all(pixel == 0 for pixel in alpha.getdata())
    elif image.info.get("transparency") is not None:
        # For palette-based images, convert to RGBA and check alpha channel
        rgba_image = image.convert("RGBA")
        alpha = rgba_image.getchannel("A")
        return all(pixel == 0 for pixel in alpha.getdata())
    
    return False



def remove_background(image: Image.Image) -> Image.Image:
    """
    Removes the background from the given PIL Image using Cloudinary's remove_background API.
    Returns a new RGBA image with the background removed.
    Raises RuntimeError if background removal fails.
    """
    try:
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Upload to Cloudinary with background removal
        response = cloudinary.uploader.upload(
            img_byte_arr,
            resource_type="image",
            type="upload",
            format="png",
            transformation=[
                {"effect": "background_removal"}
            ]
        )

        # Download the processed image
        result_url = response.get("secure_url")
        if not result_url:
            raise RuntimeError("No URL returned from Cloudinary.")

        resp = requests.get(result_url)

        if resp.status_code != 200:
            raise RuntimeError("Failed to download processed image from Cloudinary.")

        result_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        return result_img

    except Exception as e:
        raise RuntimeError(f"Failed to remove background using Cloudinary: {e}")
        


def crop_and_resize_with_outline(image: Image.Image, target_width: int = 800) -> Image.Image:
    """
    Crops all white space (fully transparent) from the edges of the image,
    resizes it to the target width while maintaining aspect ratio,
    and adds a 1px white outline around the non-transparent content.
    Raises ValueError if the image is fully transparent or invalid.
    """
    try:
        image = image.convert("RGBA")
        alpha = image.getchannel("A")
        
        # Find bounding box of non-transparent pixels
        bbox = alpha.getbbox()
        if not bbox:
            raise ValueError("Image is fully transparent or has no visible content to crop.")

        image = image.crop(bbox)

        # Resize to target width, maintain aspect ratio
        if image.width == 0 or image.height == 0:
            raise ValueError("Cropped image has zero width or height.")

        w_percent = target_width / float(image.width)
        new_height = int(float(image.height) * w_percent)
        if new_height <= 0:
            raise ValueError("Calculated new height is zero or negative.")

        image = image.resize((target_width, new_height), Image.LANCZOS)

        # Add 1px white outline
        outline_img = Image.new("RGBA", (image.width + 2, image.height + 2), (0, 0, 0, 0))
        outline_img.paste(image, (1, 1), image)

        # Draw outline
        mask = image.split()[-1]
        draw = ImageDraw.Draw(outline_img)
        for x in range(image.width):
            for y in range(image.height):
                if mask.getpixel((x, y)) > 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + 1 + dx, y + 1 + dy
                            if 0 <= nx < outline_img.width and 0 <= ny < outline_img.height:
                                if outline_img.getpixel((nx, ny))[3] == 0:
                                    outline_img.putpixel((nx, ny), (255, 255, 255, 255))
        outline_img.paste(image, (1, 1), image)

        return outline_img
    except Exception as e:
        raise RuntimeError(f"Failed to crop, resize, and outline image: {e}")
