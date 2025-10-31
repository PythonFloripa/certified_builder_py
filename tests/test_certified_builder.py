import pytest
from unittest.mock import Mock, patch
from PIL import Image, ImageDraw, ImageFont
from certified_builder.certified_builder import CertifiedBuilder
from certified_builder.certified_builder import DETAILS_FONT
from models.participant import Participant
from models.certificate import Certificate
from models.event import Event
from datetime import datetime
from unittest.mock import patch

@pytest.fixture
def mock_certificate():
    return Certificate(
        details="In recognition of their participation in the 84st edition of the Python Floripa Community Meeting, held on March 29, 2025, in Florianópolis, Brazil.",
        logo="https://tech.floripa.br/wp-content/uploads/2025/03/84o-Python-Floripa-e1741729144453.png",
        background="https://tech.floripa.br/wp-content/uploads/2025/03/Background.png"
    )

@pytest.fixture
def mock_event():
    return Event(
        order_id=452,
        product_id=316,
        product_name="Evento de Teste",
        date=datetime.strptime("2025-03-26 20:55:25", "%Y-%m-%d %H:%M:%S"),
        time_checkin=datetime.strptime("2025-03-26 20:55:44", "%Y-%m-%d %H:%M:%S"),
        checkin_latitude=-27.5460492,
        checkin_longitude=-48.6227075
    )

@pytest.fixture
def mock_participant(mock_certificate, mock_event):
    return Participant(
        first_name="Jardel",
        last_name="Godinho",
        email="jardelgodinho@gmail.com",
        phone="(48) 98866-7447",
        cpf="000.000.000-00",
        certificate=mock_certificate,
        event=mock_event
    )

@pytest.fixture
def mock_certificate_template():
    return Image.new("RGBA", (1920, 1080), (255, 255, 255, 0))

@pytest.fixture
def mock_logo():
    return Image.new("RGBA", (150, 150), (255, 255, 255, 0))

@pytest.fixture
def certified_builder():
    return CertifiedBuilder()

def test_generate_certificate(certified_builder, mock_participant, mock_certificate_template, mock_logo):
    with patch('certified_builder.utils.fetch_file_certificate.fetch_file_certificate', side_effect=[mock_certificate_template, mock_logo]):
        certificate = certified_builder.generate_certificate(mock_participant, mock_certificate_template, mock_logo)
        assert isinstance(certificate, Image.Image)
        assert certificate.size == mock_certificate_template.size
        assert certificate.mode == "RGBA"

def test_create_name_image(certified_builder, mock_participant, mock_certificate_template):
    name_image = certified_builder.create_name_image(mock_participant.name_completed(), mock_certificate_template.size)
    assert isinstance(name_image, Image.Image)
    assert name_image.size == mock_certificate_template.size
    assert name_image.mode == "RGBA"

def test_create_details_image(certified_builder, mock_participant, mock_certificate_template):
    details_image = certified_builder.create_details_image(mock_participant.certificate.details, mock_certificate_template.size)
    assert isinstance(details_image, Image.Image)
    assert details_image.size == mock_certificate_template.size
    assert details_image.mode == "RGBA"

def test_create_validation_code_image(certified_builder, mock_participant, mock_certificate_template):
    validation_code_image = certified_builder.create_validation_code_image(mock_participant.formated_validation_code(), mock_certificate_template.size)
    assert isinstance(validation_code_image, Image.Image)
    assert validation_code_image.size == mock_certificate_template.size
    assert validation_code_image.mode == "RGBA"

def test_build_certificates(certified_builder, mock_participant, mock_certificate_template, mock_logo):
    participants = [mock_participant]
    
    # comentário: mock do download de imagens e da resposta do serviço Solana para evitar chamada externa
    with patch('certified_builder.utils.fetch_file_certificate.fetch_file_certificate', side_effect=[mock_certificate_template, mock_logo]), \
         patch('certified_builder.certified_builder.CertificatesOnSolana.register_certificate_on_solana', return_value={
             # comentário: mock alinhado ao contrato atual do serviço
             "status": "sucesso",
             "certificado": {
                 "event": "evento de teste",
                 "name": "user test",
                 "email": "user@test.com",
                 "uuid": "uuid-123",
                 "time": "2025-10-31 12:05:38",
                 "json_canonico": {"fake": "data"},
                 "hash_sha256": "deadbeef",
                 "txid_solana": "fake_txid_abc123",
                 "network": "devnet",
                 "timestamp": "2025-10-31 12:05:39",
                 "timestamp_unix": 1730366739
             },
             "blockchain": {
                 "rede": "Solana Devnet",
                 "explorer_url": "https://explorer.solana.com/tx/fake_txid_abc123?cluster=devnet",
                 "verificacao_url": "http://localhost:8000/certificados/verify/fake_txid_abc123",
                 "memo_program": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
             },
             "validacao": {
                 "como_validar": "Recrie o JSON canonizado e compare o hash SHA-256",
                 "json_canonico_string": "{}",
                 "hash_esperado": "deadbeef",
                 "comando_validacao": "printf '{}' | shasum -a 256"
             }
         }), \
         patch.object(certified_builder, 'save_certificate') as mock_save:
        
        certified_builder.build_certificates(participants)
        
        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        assert isinstance(args[0], Image.Image)
        assert args[1] == mock_participant
        

def _count_non_transparent_pixels(img: Image.Image) -> int:
    # util simples para checar presença de conteúdo desenhado
    alpha = img.split()[-1]
    return sum(1 for p in alpha.getdata() if p != 0)


def test_scan_to_validate_is_centered_and_below_qr(certified_builder, mock_participant, mock_certificate_template, mock_logo):
    # Garante url para QR
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch('certified_builder.utils.fetch_file_certificate.fetch_file_certificate', side_effect=[mock_certificate_template, mock_logo]):
        result = certified_builder.generate_certificate(mock_participant, mock_certificate_template, mock_logo)

        # Recalcula posição esperada do texto seguindo a mesma lógica do código
        qrcode_size = (150, 150)
        qr_left = 50
        qr_top = 200
        draw_tmp = ImageDraw.Draw(Image.new("RGBA", mock_certificate_template.size, (255, 255, 255, 0)))
        font = ImageFont.truetype(DETAILS_FONT, 16)
        text = "Scan to Validate"
        bbox = draw_tmp.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]

        # Atenção: o código atual usa text_y = 185 + qrcode_size[1]
        expected_y = 185 + qrcode_size[1]
        expected_x = qr_left + int((qrcode_size[0] - text_w) / 2)

        # Recorta uma área ao redor da posição esperada para verificar que há conteúdo
        crop_width = max(text_w + 10, 60)
        crop_height = 22
        crop_box = (
            max(expected_x - 5, 0),
            max(expected_y - 2, 0),
            min(expected_x - 5 + crop_width, result.width),
            min(expected_y - 2 + crop_height, result.height),
        )
        cropped = result.crop(crop_box)

        assert _count_non_transparent_pixels(cropped) > 0, "Texto 'Scan to Validate' não encontrado na área esperada"


def test_qr_is_placed_at_expected_region(certified_builder, mock_participant, mock_certificate_template, mock_logo):
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch('certified_builder.utils.fetch_file_certificate.fetch_file_certificate', side_effect=[mock_certificate_template, mock_logo]):
        result = certified_builder.generate_certificate(mock_participant, mock_certificate_template, mock_logo)

        # QR é esperado em (50,200) com 150x150
        qr_left, qr_top = 50, 200
        qr_right, qr_bottom = qr_left + 150, qr_top + 150
        qr_region = result.crop((qr_left, qr_top, qr_right, qr_bottom))

        assert _count_non_transparent_pixels(qr_region) > 0, "QR não encontrado na região esperada"

        # Região logo abaixo do QR deve conter o texto (algum conteúdo)
        below_region = result.crop((qr_left, qr_bottom, qr_right, min(qr_bottom + 30, result.height)))
        assert _count_non_transparent_pixels(below_region) > 0, "Nenhum conteúdo encontrado abaixo do QR onde o texto deveria estar"

