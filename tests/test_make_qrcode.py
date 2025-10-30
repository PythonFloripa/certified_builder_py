import pytest
from io import BytesIO
from PIL import Image
from certified_builder.make_qrcode import MakeQRCode


def _count_alpha(img: Image.Image):
    a = img.split()[-1]
    zeros = sum(1 for p in a.getdata() if p == 0)
    nonzeros = sum(1 for p in a.getdata() if p != 0)
    return zeros, nonzeros


def test_generate_qr_code_returns_image_png_rgba():
    data = "https://example.com/verify/ABC123"
    byte_io = MakeQRCode.generate_qr_code(data)

    assert isinstance(byte_io, BytesIO)

    img = Image.open(byte_io)
    assert img.mode == "RGBA"
    assert img.size[0] > 0 and img.size[1] > 0


def test_qr_has_transparent_background_and_visible_foreground():
    data = "hello world"
    byte_io = MakeQRCode.generate_qr_code(data)
    img = Image.open(byte_io).convert("RGBA")

    zeros, nonzeros = _count_alpha(img)
    # Deve haver pixels transparentes (fundo) e opacos (padrão do QR)
    assert zeros > 0, "Esperava-se pixels transparentes no QR"
    assert nonzeros > 0, "Esperava-se pixels opacos no QR"


