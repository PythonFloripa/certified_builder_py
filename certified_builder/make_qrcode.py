
import qrcode
import logging
from io import BytesIO
from qrcode.image.pil import PilImage

logger = logging.getLogger(__name__)

class MakeQRCode:
    @staticmethod
    def generate_qr_code(data: str) -> BytesIO:
        try:
            logger.info("Generating QR code ")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="transparent", image_factory=PilImage)
            img = img.convert("RGBA")
            byte_io = BytesIO()
            img.save(byte_io, format='PNG')
            byte_io.seek(0)
            logger.info("QR code generated successfully")
            return byte_io
        except Exception as e:
            logging.error(f"Failed to generate QR code: {e}")
            raise