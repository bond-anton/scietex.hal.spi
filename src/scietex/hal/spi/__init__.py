"""SPI bus transport backends for scietex.hal devices."""

from typing import TYPE_CHECKING, Any

from .base import (
    I2cTransport,
    SpiTransport,
    TransportClosed,
    TransportError,
    is_spi_transport,
)
from .fake import FakeSpiTransport
from .gpiozero_helpers import fix_gpiozero_dual_cs_spi
from .selection import (
    GPIOZERO_PIN_ARGS,
    GPIOZERO_SPI_ARGS,
    build_default_transport,
)
from .spidev_spi import SpiDevTransport
from .version import __version__ as __version__

if TYPE_CHECKING:
    from .gpiozero_spi import GpiozeroSpiTransport  # noqa: F401

#: Names resolved lazily by `__getattr__`; kept out of `__all__` so a star
#: import works on a core install without the optional gpiozero package.
_LAZY_ATTRIBUTES = ("GpiozeroSpiTransport",)

__all__ = [
    "FakeSpiTransport",
    "GPIOZERO_PIN_ARGS",
    "GPIOZERO_SPI_ARGS",
    "I2cTransport",
    "SpiDevTransport",
    "SpiTransport",
    "TransportClosed",
    "TransportError",
    "build_default_transport",
    "fix_gpiozero_dual_cs_spi",
    "is_spi_transport",
]


def __getattr__(name: str) -> Any:
    """Resolve the optional gpiozero transport on first access."""
    if name == "GpiozeroSpiTransport":
        try:
            from .gpiozero_spi import GpiozeroSpiTransport  # noqa: PLC0415
        except ImportError as exc:
            raise AttributeError(
                "GpiozeroSpiTransport requires the optional 'gpiozero' package. "
                "Install it with: pip install 'scietex.hal.spi[gpiozero]'"
            ) from exc

        return GpiozeroSpiTransport
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List the module attributes, including lazily resolved names."""
    return sorted(set(__all__) | set(globals()) | set(_LAZY_ATTRIBUTES))
