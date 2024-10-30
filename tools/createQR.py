import qrcode
from aiogram.types import FSInputFile
from qrcode.main import QRCode


def generate_qr_code(url: str, path: str = "qrcode.png"):
    """Создает QR-код на основе URL и сохраняет его как изображение."""
    qr = QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)
    return FSInputFile(path)