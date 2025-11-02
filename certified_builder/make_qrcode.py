
import qrcode
import logging
from io import BytesIO
from PIL import Image
from qrcode.image.pil import PilImage

logger = logging.getLogger(__name__)

class MakeQRCode:
    @staticmethod
    def generate_qr_code(data: str, logo_tech_floripa: Image) -> BytesIO:        
        try:
            logger.info(f"Generating QR code for {data}")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )

            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="transparent", image_factory=PilImage)
            img = img.convert("RGBA")
            
            # Redimensiona o logo para aproximadamente 30% do tamanho do QR code
            # Tamanho limitado para não interferir nos padrões de detecção nos cantos
            qr_width, qr_height = img.size
            logo_size = int(min(qr_width, qr_height) * 0.3)
            logo_resized = logo_tech_floripa.copy()
            logo_resized.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            logo_resized = logo_resized.convert("RGBA")
            
            # Calcula a posição central para colar o logo
            logo_width, logo_height = logo_resized.size
            position = ((qr_width - logo_width) // 2, (qr_height - logo_height) // 2)
            
            # Cola o logo no centro do QR code mantendo transparência
            # Com ERROR_CORRECT_H (30% redundância), o QR code permanece legível mesmo com o logo
            img.paste(logo_resized, position, logo_resized)
            
            byte_io = BytesIO()
            img.save(byte_io, format='PNG')
            byte_io.seek(0)
            logger.info(f"QR code generated successfully for {data}")
            return byte_io
        except Exception as e:
            logging.error(f"Failed to generate QR code: {e}")
            raise