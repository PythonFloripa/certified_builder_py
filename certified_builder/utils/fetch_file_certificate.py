from PIL import Image
from io import BytesIO
import httpx
import os


def fetch_file_certificate(url_certificate) -> Image:
    # Configure client for Lambda environment
    client = httpx.Client(
        timeout=30.0,
        verify=False,  # Disable SSL verification if needed
        follow_redirects=True,
    )

    try:
        response = client.get(url_certificate)
        response.raise_for_status()  # Raise an exception for bad status codes
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        raise Exception(f"Error fetching certificate: {str(e)}")
    finally:
        client.close()
