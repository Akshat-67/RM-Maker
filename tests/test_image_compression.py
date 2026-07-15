import io
from PIL import Image
from utils.helpers import prepare_image_for_nim

def test_prepare_image():
    # Create a large dummy image
    img = Image.new('RGB', (1000, 1000), color = 'red')
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    png_bytes = byte_arr.getvalue()
    
    b64_str = prepare_image_for_nim(png_bytes)
    assert len(b64_str) < 180000
    assert b64_str.startswith("data:image/jpeg;base64,")
