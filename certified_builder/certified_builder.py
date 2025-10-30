import logging
import tempfile
import os
from typing import List
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from models.participant import Participant
from certified_builder.utils.fetch_file_certificate import fetch_file_certificate
from certified_builder.certificates_on_solana import CertificatesOnSolana
from certified_builder.make_qrcode import MakeQRCode
from certified_builder.build_url_tech_floripa import build_url_tech_floripa

FONT_NAME = os.path.join(os.path.dirname(__file__), "fonts/PinyonScript/PinyonScript-Regular.ttf")
VALIDATION_CODE = os.path.join(os.path.dirname(__file__), "fonts/ChakraPetch/ChakraPetch-SemiBold.ttf")
DETAILS_FONT = os.path.join(os.path.dirname(__file__), "fonts/ChakraPetch/ChakraPetch-Regular.ttf")
TEXT_COLOR = (0, 0, 0)

logger = logging.getLogger(__name__)

class CertifiedBuilder:
    def __init__(self):
        # Ensure temp directory exists
        self.temp_dir = "/tmp/certificates"
        os.makedirs(self.temp_dir, exist_ok=True)

        
    def build_certificates(self, participants: List[Participant]):
        """Build certificates for all participants."""
        try:
            logger.info(f"Iniciando geração de {len(participants)} certificados")
            results = []
            
            # Cache for background and logo if they are the same for all participants
            certificate_template = None
            logo = None
            
            # Check if all participants share the same background and logo
            if participants:
                first_participant = participants[0]
                all_same_background = all(p.certificate.background == first_participant.certificate.background for p in participants)
                all_same_logo = all(p.certificate.logo == first_participant.certificate.logo for p in participants)
                
                # Download shared resources once if they are the same for all
                if all_same_background:
                    certificate_template = self._download_image(first_participant.certificate.background)
                if all_same_logo:
                    logo = self._download_image(first_participant.certificate.logo)
            
            for participant in participants:
                try:
                    # Register certificate on Solana, with returned data extract url for verification
                    solana_response = CertificatesOnSolana.register_certificate_on_solana(
                        certificate_data={
                            "name": participant.name_completed(),
                            "event": participant.event.product_name,
                            "email": participant.email,
                            "certificate_code": participant.formated_validation_code()
                        }
                    )
                    # solana_response = {
                    #     "blockchain": {
                    #         "verificacao_url": "https://www.google.com"
                    #     }
                    # }
                                                            
                    participant.authenticity_verification_url = build_url_tech_floripa(
                        url_service_solona=solana_response.get("blockchain", {}).get("verificacao_url", ""),
                        validation_code=participant.formated_validation_code(),
                        order_id=participant.event.order_id
                    )
                    
                    if not participant.authenticity_verification_url:                        
                        raise RuntimeError("Failed to get authenticity verification URL from Solana response")

                    # Download template and logo only if they are not shared
                    if not all_same_background:
                        certificate_template = self._download_image(participant.certificate.background)
                    if not all_same_logo:
                        logo = self._download_image(participant.certificate.logo)
                    
                    # Generate and save certificate
                    certificate_generated = self.generate_certificate(participant, certificate_template, logo)
                    certificate_path = self.save_certificate(certificate_generated, participant)
                    
                    results.append({
                        "participant": participant.model_dump(),
                        "certificate_path": certificate_path,
                        "certificate_key": f"certificates/{participant.event.product_id}/{participant.event.order_id}/{participant.create_name_certificate()}",
                        "success": True
                    })
                                        
                    logger.info(f"Certificado gerado para {participant.name_completed()} com codigo de validação {participant.formated_validation_code()}")
                except Exception as e:
                    logger.error(f"Erro ao gerar certificado para {participant.name_completed()}: {str(e)}")
                    results.append({
                        "participant": participant.model_dump(),
                        "error": str(e),
                        "success": False
                    })
                
            return results
        except Exception as e:
            logger.error(f"Erro geral na geração de certificados: {str(e)}")
            raise

    def _download_image(self, url: str) -> Image:
        """Download and open image with error handling."""
        try:
            return fetch_file_certificate(url)
        except Exception as e:
            logger.error(f"Erro ao baixar imagem de {url}: {str(e)}")
            raise RuntimeError(f"Error downloading image from {url}: {str(e)}")

    def _ensure_valid_rgba(self, img: Image) -> Image:
        """Ensure image has a valid RGBA mode with proper transparency channel."""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Some PNG images may have problematic transparency channels
        # Create a new image with proper alpha channel
        try:
            new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
            new_img.paste(img, (0, 0), img if 'A' in img.mode else None)
            return new_img
        except Exception as e:
            logger.warning(f"Erro ao processar transparência, usando método alternativo: {str(e)}")
            # Fallback method if there's an issue with the alpha channel
            new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
            new_img.paste(img.convert('RGB'), (0, 0))
            return new_img

    def generate_certificate(self, participant: Participant, certificate_template: Image, logo: Image):
        """Generate a certificate for a participant."""
        try:
            # Ensure images have valid transparency channels
            certificate_template = self._ensure_valid_rgba(certificate_template)
            logo = self._ensure_valid_rgba(logo)
            
            # Create transparent layer for text and logo
            overlay = Image.new("RGBA", certificate_template.size, (255, 255, 255, 0))
            
            # Optimize logo size (evita upscaling para reduzir pixelização)
            logo_max_size = (150, 150)
            if logo.width > logo_max_size[0] or logo.height > logo_max_size[1]:
                logo.thumbnail(logo_max_size, Image.Resampling.LANCZOS)
            
            # Paste logo - handle potential transparency issues
            try:
                # Try with mask first
                overlay.paste(logo, (50, 50), logo)
            except Exception as e:
                logger.warning(f"Erro ao colar logo com máscara, usando método alternativo: {str(e)}")
                # Fallback without using the logo as its own mask
                overlay.paste(logo, (50, 50))
            
           
            qrcode_size = (150, 150)                       
            qr_code_image_io = MakeQRCode.generate_qr_code(participant.authenticity_verification_url)            
            qr_code_image = Image.open(qr_code_image_io).convert("RGBA")            
            # comentário: para manter o QR nítido, usamos NEAREST ao redimensionar
            if qr_code_image.size != qrcode_size:
                qr_code_image = qr_code_image.resize(qrcode_size, Image.Resampling.NEAREST)
            
            # Add QR code to overlay
            # preciso que a posição do QR code seja abaixo do logo, alinhado à esquerda
            overlay.paste(qr_code_image, (50, 200), qr_code_image)

            # Add "Scan to Validate" text below the QR code
            # comentário: camada de texto criada para ficar logo abaixo do QR code, centralizada ao QR e com espaçamento justo
            try:
                # calcula centralização do texto com base na largura do QR
                tmp_img = Image.new("RGBA", certificate_template.size, (255, 255, 255, 0))
                tmp_draw = ImageDraw.Draw(tmp_img)
                tmp_font = ImageFont.truetype(DETAILS_FONT, 16)
                text_bbox = tmp_draw.textbbox((0, 0), "Scan to Validate", font=tmp_font)
                text_w = text_bbox[2] - text_bbox[0]
                text_x = 50 + int((qrcode_size[0] - text_w) / 2)
                text_y = 185 + qrcode_size[1]  # espaçamento curto (quase colado)

                scan_text_image = self.create_scan_to_validate_image(
                    size=certificate_template.size,
                    position=(text_x, text_y)
                )
                overlay.paste(scan_text_image, (0, 0), scan_text_image)
                logger.info("Texto 'Scan to Validate' adicionado abaixo do QR code")
            except Exception as e:
                logger.warning(f"Falha ao adicionar texto 'Scan to Validate': {str(e)}")


            # Add name
            name_image = self.create_name_image(participant.name_completed(), certificate_template.size)
            
            # Paste with error handling
            try:
                overlay.paste(name_image, (0, 0), name_image)
            except Exception as e:
                logger.warning(f"Erro ao colar nome com máscara, usando método alternativo: {str(e)}")
                # Try without mask
                overlay.paste(name_image, (0, 0))
            
            # Add details
            details_image = self.create_details_image(participant.certificate.details, certificate_template.size)
            name_center_y = certificate_template.size[1] // 2
            details_y = name_center_y + 50
            
            details_with_position = Image.new("RGBA", certificate_template.size, (255, 255, 255, 0))
            
            # Paste with error handling
            try:
                details_with_position.paste(details_image, (0, details_y), details_image)
            except Exception as e:
                logger.warning(f"Erro ao colar detalhes com máscara, usando método alternativo: {str(e)}")
                details_with_position.paste(details_image, (0, details_y))
            
            try:
                overlay = Image.alpha_composite(overlay, details_with_position)
            except Exception as e:
                logger.warning(f"Erro na composição alpha, usando método alternativo: {str(e)}")
                # Fallback to simple paste if alpha composite fails
                overlay.paste(details_with_position, (0, 0))
            
            # Add validation code
            validation_code_image = self.create_validation_code_image(participant.formated_validation_code(), certificate_template.size)
            
            try:
                overlay.paste(validation_code_image, (0, 0), validation_code_image)
            except Exception as e:
                logger.warning(f"Erro ao colar código de validação com máscara, usando método alternativo: {str(e)}")
                overlay.paste(validation_code_image, (0, 0))
            
            # Merge and optimize final image
            result = Image.new("RGBA", certificate_template.size, (255, 255, 255, 0))
            result.paste(certificate_template, (0, 0))
            
            try:
                result = Image.alpha_composite(result, overlay)
            except Exception as e:
                logger.warning(f"Erro na composição alpha final, usando método alternativo: {str(e)}")
                # Fallback to simple paste if alpha composite fails
                result.paste(overlay, (0, 0))
            
            return result
        except Exception as e:
            logger.error(f"Erro ao gerar certificado: {str(e)}")
            raise

    def create_name_image(self, name: str, size: tuple) -> Image:
        """Create image with participant's name."""
        try:
            name_image = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(name_image)
            font = ImageFont.truetype(FONT_NAME, 70)
            position = self.calculate_text_position(name, font, draw, size)
            draw.text(position, name, fill=TEXT_COLOR, font=font)
            return name_image
        except Exception as e:
            logger.error(f"Erro ao criar imagem do nome: {str(e)}")
            raise

    def create_details_image(self, details: str, size: tuple) -> Image:
        """Create image with certificate details."""
        try:
            details_image = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(details_image)
            font = ImageFont.truetype(DETAILS_FONT, 18)

            words = details.split()
            total_words = len(words)
            words_per_line = total_words // 3
            
            line1 = ' '.join(words[:words_per_line])
            line2 = ' '.join(words[words_per_line:words_per_line*2])
            line3 = ' '.join(words[words_per_line*2:])
            
            line_height = font.size + 10
            
            line1_bbox = draw.textbbox((0, 0), line1, font=font)
            line2_bbox = draw.textbbox((0, 0), line2, font=font)
            line3_bbox = draw.textbbox((0, 0), line3, font=font)
            
            start_y = 0
            
            x1 = (size[0] - (line1_bbox[2] - line1_bbox[0])) / 2
            x2 = (size[0] - (line2_bbox[2] - line2_bbox[0])) / 2
            x3 = (size[0] - (line3_bbox[2] - line3_bbox[0])) / 2
            
            draw.text((x1, start_y), line1, fill=TEXT_COLOR, font=font)
            draw.text((x2, start_y + line_height), line2, fill=TEXT_COLOR, font=font)
            draw.text((x3, start_y + line_height * 2), line3, fill=TEXT_COLOR, font=font)
            
            return details_image
        except Exception as e:
            logger.error(f"Erro ao criar imagem dos detalhes: {str(e)}")
            raise

    def create_validation_code_image(self, validation_code: str, size: tuple) -> Image:
        """Create image with validation code."""
        try:
            validation_code_image = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(validation_code_image)
            font = ImageFont.truetype(VALIDATION_CODE, 20)
            position = self.calculate_validation_code_position(validation_code, font, draw, size)
            draw.text(position, validation_code, fill=TEXT_COLOR, font=font)
            return validation_code_image
        except Exception as e:
            logger.error(f"Erro ao criar imagem do código de validação: {str(e)}")
            raise

    def create_scan_to_validate_image(self, size: tuple, position: tuple) -> Image:
        """Create image with the 'Scan to Validate' label using DETAILS_FONT at a given position."""
        try:
            # comentário: imagem transparente do tamanho do canvas com o texto posicionado
            text_image = Image.new("RGBA", size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_image)
            font = ImageFont.truetype(DETAILS_FONT, 16)
            draw.text(position, "Scan to Validate", fill=TEXT_COLOR, font=font)
            return text_image
        except Exception as e:
            logger.error(f"Erro ao criar imagem do texto 'Scan to Validate': {str(e)}")
            raise

    def calculate_text_position(self, text: str, font: ImageFont, draw: ImageDraw, size: tuple) -> tuple:
        """Calculate centered position for text."""
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        return ((size[0] - text_width) / 2, (size[1] - text_height) / 2)

    def calculate_validation_code_position(self, validation_code: str, font: ImageFont, draw: ImageDraw, size: tuple) -> tuple:
        """Calculate position for validation code."""
        text_bbox = draw.textbbox((0, 0), validation_code, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        return (size[0] - text_width - 50, size[1] - text_height - 40)

    def save_certificate(self, certificate: Image, participant: Participant) -> str:
        """Save certificate to temporary directory."""
        try:
            name_certificate = participant.create_name_certificate()
            file_path = os.path.join(self.temp_dir, name_certificate)
            # Optimize image before saving
            certificate = certificate.convert('RGB')
            certificate.save(file_path, format="PNG", optimize=True)            
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar certificado: {str(e)}")
            raise
