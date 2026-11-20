"""QR codes for opening the phone page (qrcode, BSD)."""

from __future__ import annotations

import io


def qr_svg(url: str) -> str:
    import qrcode
    from qrcode.image.svg import SvgPathImage

    image = qrcode.make(url, image_factory=SvgPathImage, box_size=10, border=2)
    return image.to_string(encoding="unicode")


def qr_ascii(url: str) -> str:
    """A QR code drawn with block characters, for the console."""
    import qrcode

    code = qrcode.QRCode(border=1)
    code.add_data(url)
    code.make(fit=True)
    out = io.StringIO()
    code.print_ascii(out=out, invert=True)
    return out.getvalue()
