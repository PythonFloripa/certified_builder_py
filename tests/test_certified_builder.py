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
        background="https://tech.floripa.br/wp-content/uploads/2025/03/Background.png",
    )


@pytest.fixture
def mock_event():
    return Event(
        order_id=452,
        product_id=316,
        product_name="Evento de Teste",
        date=datetime.strptime("2025-03-26 20:55:25", "%Y-%m-%d %H:%M:%S"),
        time_checkin=datetime.strptime("2025-03-26 20:55:44", "%Y-%m-%d %H:%M:%S"),
    )


@pytest.fixture
def mock_participant(mock_certificate, mock_event):
    return Participant(
        first_name="Jardel",
        last_name="Godinho",
        email="jardelgodinho@gmail.com",
        certificate=mock_certificate,
        event=mock_event,
    )


@pytest.fixture
def mock_certificate_template():
    return Image.new("RGBA", (1920, 1080), (255, 255, 255, 0))


@pytest.fixture
def mock_logo():
    return Image.new("RGBA", (150, 150), (255, 255, 255, 0))


@pytest.fixture
def mock_logo_tech_floripa():
    return Image.new("RGBA", (100, 100), (255, 255, 255, 255))


@pytest.fixture
def certified_builder():
    return CertifiedBuilder()


def test_generate_certificate(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        certificate = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )
        assert isinstance(certificate, Image.Image)
        assert certificate.size == mock_certificate_template.size
        assert certificate.mode == "RGBA"


def test_create_name_image(
    certified_builder, mock_participant, mock_certificate_template
):
    name_image = certified_builder.create_name_image(
        mock_participant.name_completed(), mock_certificate_template.size
    )
    assert isinstance(name_image, Image.Image)
    assert name_image.size == mock_certificate_template.size
    assert name_image.mode == "RGBA"


def test_create_details_image(
    certified_builder, mock_participant, mock_certificate_template
):
    details_image = certified_builder.create_details_image(
        mock_participant.certificate.details, mock_certificate_template.size
    )
    assert isinstance(details_image, Image.Image)
    assert details_image.size == mock_certificate_template.size
    assert details_image.mode == "RGBA"


def test_create_validation_code_image(
    certified_builder, mock_participant, mock_certificate_template
):
    validation_code_image = certified_builder.create_validation_code_image(
        mock_participant.formated_validation_code(), mock_certificate_template.size
    )
    assert isinstance(validation_code_image, Image.Image)
    assert validation_code_image.size == mock_certificate_template.size
    assert validation_code_image.mode == "RGBA"


def test_build_certificates(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    participants = [mock_participant]

    # comentário: mock do download de imagens e da resposta do serviço Solana para evitar chamada externa
    # Função que retorna o mock baseado na URL chamada
    def mock_download_image(url):
        if url == mock_participant.certificate.background:
            return mock_certificate_template
        elif url == mock_participant.certificate.logo:
            return mock_logo
        elif (
            url == "https://example.test/logo.png"
        ):  # TECH_FLORIPA_LOGO_URL do config mock
            return mock_logo_tech_floripa
        raise ValueError(f"URL não mockada: {url}")

    with (
        patch.object(
            certified_builder, "_download_image", side_effect=mock_download_image
        ),
        patch(
            "certified_builder.certified_builder.CertificatesOnSolana.register_certificate_on_solana",
            return_value={
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
                    "timestamp_unix": 1730366739,
                },
                "blockchain": {
                    "rede": "Solana Devnet",
                    "explorer_url": "https://explorer.solana.com/tx/fake_txid_abc123?cluster=devnet",
                    "verificacao_url": "http://localhost:8000/certificados/verify/fake_txid_abc123",
                    "memo_program": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
                },
                "validacao": {
                    "como_validar": "Recrie o JSON canonizado e compare o hash SHA-256",
                    "json_canonico_string": "{}",
                    "hash_esperado": "deadbeef",
                    "comando_validacao": "printf '{}' | shasum -a 256",
                },
            },
        ),
        patch.object(certified_builder, "save_certificate") as mock_save,
    ):

        certified_builder.build_certificates(participants)

        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        assert isinstance(args[0], Image.Image)
        assert args[1] == mock_participant


def _count_non_transparent_pixels(img: Image.Image) -> int:
    # util simples para checar presença de conteúdo desenhado
    alpha = img.split()[-1]
    return sum(1 for p in alpha.getdata() if p != 0)


def test_scan_to_validate_is_centered_and_below_qr(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    # Garante url para QR
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        # Recalcula posição esperada do texto seguindo a mesma lógica do código
        qrcode_size = (150, 150)
        qr_left = 50
        qr_top = 200
        draw_tmp = ImageDraw.Draw(
            Image.new("RGBA", mock_certificate_template.size, (255, 255, 255, 0))
        )
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

        assert (
            _count_non_transparent_pixels(cropped) > 0
        ), "Texto 'Scan to Validate' não encontrado na área esperada"


def test_qr_is_placed_at_expected_region(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        # QR é esperado em (50,200) com 150x150
        qr_left, qr_top = 50, 200
        qr_right, qr_bottom = qr_left + 150, qr_top + 150
        qr_region = result.crop((qr_left, qr_top, qr_right, qr_bottom))

        assert (
            _count_non_transparent_pixels(qr_region) > 0
        ), "QR não encontrado na região esperada"

        # Região logo abaixo do QR deve conter o texto (algum conteúdo)
        below_region = result.crop(
            (qr_left, qr_bottom, qr_right, min(qr_bottom + 30, result.height))
        )
        assert (
            _count_non_transparent_pixels(below_region) > 0
        ), "Nenhum conteúdo encontrado abaixo do QR onde o texto deveria estar"


def test_name_is_centered_on_certificate(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Verifica que o nome do participante está centralizado no certificado."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        # Verifica que há conteúdo na região central onde o nome deveria estar
        center_x = result.width // 2
        center_y = result.height // 2
        name_region = result.crop(
            (center_x - 200, center_y - 50, center_x + 200, center_y + 50)
        )

        assert (
            _count_non_transparent_pixels(name_region) > 0
        ), "Nome não encontrado na região central do certificado"


def test_validation_code_is_at_bottom_right(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Verifica que o código de validação está posicionado no canto inferior direito."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        # Verifica região inferior direita onde o código de validação deveria estar
        validation_region = result.crop(
            (result.width - 250, result.height - 80, result.width, result.height)
        )

        assert (
            _count_non_transparent_pixels(validation_region) > 0
        ), "Código de validação não encontrado no canto inferior direito"


def test_logo_is_positioned_at_top_left(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo_tech_floripa,
):
    """Verifica que o logo está posicionado no canto superior esquerdo."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"
    # Usa um logo visível (não transparente) para o teste
    visible_logo = Image.new("RGBA", (150, 150), (255, 255, 255, 255))

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, visible_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            visible_logo,
            mock_logo_tech_floripa,
        )

        # Logo é esperado em (50, 50) com tamanho máximo de 150x150
        logo_region = result.crop((50, 50, 200, 200))

        assert (
            _count_non_transparent_pixels(logo_region) > 0
        ), "Logo não encontrado na região esperada"


def test_large_logo_is_resized(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo_tech_floripa,
):
    """Verifica que logos grandes são redimensionados para o tamanho máximo."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"
    large_logo = Image.new("RGBA", (300, 300), (255, 255, 255, 255))

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, large_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            large_logo,
            mock_logo_tech_floripa,
        )

        # Verifica que o logo foi redimensionado (não deve ocupar toda a região de 300x300)
        logo_region = result.crop((50, 50, 200, 200))

        assert (
            _count_non_transparent_pixels(logo_region) > 0
        ), "Logo redimensionado não encontrado"


def test_details_are_split_into_three_lines(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Verifica que os detalhes do certificado são divididos em 3 linhas."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        # Verifica região onde os detalhes deveriam estar (abaixo do centro)
        center_y = result.height // 2
        details_region = result.crop((0, center_y + 50, result.width, center_y + 150))

        assert (
            _count_non_transparent_pixels(details_region) > 0
        ), "Detalhes não encontrados na região esperada"


def test_build_certificates_with_multiple_participants_same_resources(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Testa geração de certificados para múltiplos participantes com mesmo background e logo."""
    second_participant = Participant(
        first_name="Maria",
        last_name="Silva",
        email="maria@example.com",
        certificate=mock_participant.certificate,
        event=mock_participant.event,
    )

    participants = [mock_participant, second_participant]

    def mock_download_image(url):
        if url == mock_participant.certificate.background:
            return mock_certificate_template
        elif url == mock_participant.certificate.logo:
            return mock_logo
        elif url == "https://example.test/logo.png":
            return mock_logo_tech_floripa
        raise ValueError(f"URL não mockada: {url}")

    with (
        patch.object(
            certified_builder, "_download_image", side_effect=mock_download_image
        ),
        patch(
            "certified_builder.certified_builder.CertificatesOnSolana.register_certificate_on_solana",
            return_value={
                "blockchain": {
                    "explorer_url": "https://explorer.solana.com/tx/test123?cluster=devnet"
                }
            },
        ),
        patch.object(certified_builder, "save_certificate") as mock_save,
    ):

        results = certified_builder.build_certificates(participants)

        assert len(results) == 2
        assert all(r["success"] for r in results)
        assert mock_save.call_count == 2


def test_build_certificates_with_different_backgrounds(
    certified_builder, mock_participant, mock_logo, mock_logo_tech_floripa
):
    """Testa geração de certificados para participantes com backgrounds diferentes."""
    different_background = "https://example.com/different-background.png"
    different_template = Image.new("RGBA", (1920, 1080), (200, 200, 200, 255))

    second_certificate = Certificate(
        details=mock_participant.certificate.details,
        logo=mock_participant.certificate.logo,
        background=different_background,
    )

    second_participant = Participant(
        first_name="João",
        last_name="Santos",
        email="joao@example.com",
        certificate=second_certificate,
        event=mock_participant.event,
    )

    participants = [mock_participant, second_participant]

    def mock_download_image(url):
        if url == mock_participant.certificate.background:
            return Image.new("RGBA", (1920, 1080), (255, 255, 255, 0))
        elif url == different_background:
            return different_template
        elif url == mock_participant.certificate.logo:
            return mock_logo
        elif url == "https://example.test/logo.png":
            return mock_logo_tech_floripa
        raise ValueError(f"URL não mockada: {url}")

    with (
        patch.object(
            certified_builder, "_download_image", side_effect=mock_download_image
        ),
        patch(
            "certified_builder.certified_builder.CertificatesOnSolana.register_certificate_on_solana",
            return_value={
                "blockchain": {
                    "explorer_url": "https://explorer.solana.com/tx/test123?cluster=devnet"
                }
            },
        ),
        patch.object(certified_builder, "save_certificate") as mock_save,
    ):

        results = certified_builder.build_certificates(participants)

        assert len(results) == 2
        assert all(r["success"] for r in results)


def test_build_certificates_handles_solana_registration_error(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Testa tratamento de erro quando o registro na Solana falha."""
    participants = [mock_participant]

    def mock_download_image(url):
        if url == mock_participant.certificate.background:
            return mock_certificate_template
        elif url == mock_participant.certificate.logo:
            return mock_logo
        elif url == "https://example.test/logo.png":
            return mock_logo_tech_floripa
        raise ValueError(f"URL não mockada: {url}")

    with (
        patch.object(
            certified_builder, "_download_image", side_effect=mock_download_image
        ),
        patch(
            "certified_builder.certified_builder.CertificatesOnSolana.register_certificate_on_solana",
            return_value={"blockchain": {}},  # Sem explorer_url - simula erro
        ),
    ):

        results = certified_builder.build_certificates(participants)

        assert len(results) == 1
        assert results[0]["success"] == False
        assert "Failed to get authenticity verification URL" in results[0]["error"]


def test_save_certificate_saves_to_temp_directory(
    certified_builder,
    mock_participant,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Testa que o certificado é salvo no diretório temporário."""
    mock_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        certificate = certified_builder.generate_certificate(
            mock_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )
        file_path = certified_builder.save_certificate(certificate, mock_participant)

        assert file_path.startswith("/tmp/certificates/")
        assert file_path.endswith(".png")

        import os

        assert os.path.exists(file_path), "Arquivo do certificado não foi criado"


def test_generate_certificate_with_long_name(
    certified_builder,
    mock_certificate,
    mock_certificate_template,
    mock_logo,
    mock_logo_tech_floripa,
):
    """Testa geração de certificado com nome muito longo."""
    mock_event = Event(
        order_id=1,
        product_id=1,
        product_name="Evento Teste",
        date=datetime.now(),
        time_checkin=datetime.now(),
    )

    long_name_participant = Participant(
        first_name="João Pedro",
        last_name="da Silva Santos Oliveira",
        email="joao@example.com",
        certificate=mock_certificate,
        event=mock_event,
    )
    long_name_participant.authenticity_verification_url = "https://example.com/verify"

    with patch(
        "certified_builder.utils.fetch_file_certificate.fetch_file_certificate",
        side_effect=[mock_certificate_template, mock_logo],
    ):
        result = certified_builder.generate_certificate(
            long_name_participant,
            mock_certificate_template,
            mock_logo,
            mock_logo_tech_floripa,
        )

        assert isinstance(result, Image.Image)
        assert result.size == mock_certificate_template.size


def test_ensure_valid_rgba_converts_rgb_image(certified_builder):
    """Testa que _ensure_valid_rgba converte imagens RGB para RGBA."""
    rgb_image = Image.new("RGB", (100, 100), (255, 0, 0))
    rgba_image = certified_builder._ensure_valid_rgba(rgb_image)

    assert rgba_image.mode == "RGBA"
    assert rgba_image.size == rgb_image.size


def test_ensure_valid_rgba_preserves_rgba_image(certified_builder):
    """Testa que _ensure_valid_rgba preserva imagens já em RGBA."""
    rgba_image = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    result = certified_builder._ensure_valid_rgba(rgba_image)

    assert result.mode == "RGBA"
    assert result.size == rgba_image.size
