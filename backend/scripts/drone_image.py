import asyncio
import sys
from pathlib import Path

async def process_drone_images(nir_bytes: bytes, img_bytes: bytes):
    # nir_bytes: the NIR image file content (JPEG)
    # img_bytes: the RGB image file content (JPEG)
    # 
    #ndvi here pls ! (or just reuse this somewhere else idm)
    return {
        "nir_size": len(nir_bytes),
        "img_size": len(img_bytes)
    }

    