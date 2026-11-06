"""Optional backend isolation: the core install needs no gpiozero or spidev."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"


def _run_isolated(code: str) -> subprocess.CompletedProcess:
    """Run `code` in a fresh interpreter rooted at the package sources."""
    bootstrap = f"import sys\nsys.path.insert(0, {str(SOURCE_ROOT)!r})\n"
    return subprocess.run(
        [sys.executable, "-c", bootstrap + code],
        cwd=str(SOURCE_ROOT.parent),
        capture_output=True,
        text=True,
        check=False,
    )


class TestOptionalBackends(unittest.TestCase):
    """The package imports and runs without the optional SPI backends."""

    def assert_ran(self, result: subprocess.CompletedProcess) -> None:
        """Fail with the subprocess stderr when its script did not finish."""
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ok", result.stderr)

    def test_import_does_not_load_optional_backends(self):
        """Importing the package and its helper module loads neither backend."""
        result = _run_isolated(
            "import scietex.hal.spi\n"
            "import scietex.hal.spi.gpiozero_helpers\n"
            "loaded = [name for name in ('gpiozero', 'spidev') "
            "if name in sys.modules]\n"
            "if loaded:\n"
            "    raise SystemExit(f'importing the package loaded {loaded}')\n"
            "print('ok')\n"
        )
        self.assert_ran(result)

    def test_missing_spidev_names_the_spi_extra(self):
        """Building the spidev backend without spidev names the spi extra."""
        result = _run_isolated(
            "sys.modules['spidev'] = None\n"
            "from scietex.hal.spi import SpiDevTransport\n"
            "try:\n"
            "    SpiDevTransport()\n"
            "except ImportError as exc:\n"
            "    if 'scietex.hal.spi[spi]' not in str(exc):\n"
            "        raise SystemExit(f'unexpected message: {exc}')\n"
            "    print('ok')\n"
            "else:\n"
            "    raise SystemExit('SpiDevTransport did not raise ImportError')\n"
        )
        self.assert_ran(result)

    def test_missing_gpiozero_names_the_gpiozero_extra(self):
        """A pin keyword without gpiozero raises ImportError naming its extra."""
        result = _run_isolated(
            "sys.modules['gpiozero'] = None\n"
            "from scietex.hal.spi import build_default_transport\n"
            "try:\n"
            "    build_default_transport(clock_pin=11)\n"
            "except ImportError as exc:\n"
            "    if 'scietex.hal.spi[gpiozero]' not in str(exc):\n"
            "        raise SystemExit(f'unexpected message: {exc}')\n"
            "    print('ok')\n"
            "else:\n"
            "    raise SystemExit('build_default_transport did not raise ImportError')\n"
        )
        self.assert_ran(result)

    def test_missing_gpiozero_hides_transport_attribute(self):
        """Without gpiozero, hasattr is False and dir still advertises the name."""
        result = _run_isolated(
            "sys.modules['gpiozero'] = None\n"
            "import scietex.hal.spi as spi\n"
            "if hasattr(spi, 'GpiozeroSpiTransport'):\n"
            "    raise SystemExit('package exposes GpiozeroSpiTransport')\n"
            "if 'GpiozeroSpiTransport' not in dir(spi):\n"
            "    raise SystemExit('package does not advertise GpiozeroSpiTransport')\n"
            "try:\n"
            "    spi.GpiozeroSpiTransport\n"
            "except AttributeError as exc:\n"
            "    if 'scietex.hal.spi[gpiozero]' not in str(exc):\n"
            "        raise SystemExit(f'unexpected message: {exc}')\n"
            "else:\n"
            "    raise SystemExit('GpiozeroSpiTransport resolved without gpiozero')\n"
            "print('ok')\n"
        )
        self.assert_ran(result)

    def test_gpiozero_transport_resolves_when_available(self):
        """With gpiozero installed, the lazy resolver returns the class."""
        if importlib.util.find_spec("gpiozero") is None:
            self.skipTest("gpiozero is not installed")

        import scietex.hal.spi as spi

        self.assertIsInstance(spi.GpiozeroSpiTransport, type)

    def test_fake_transport_works_without_both_backends(self):
        """The scripted transport stays usable without either backend."""
        result = _run_isolated(
            "sys.modules['spidev'] = None\n"
            "sys.modules['gpiozero'] = None\n"
            "from scietex.hal.spi import FakeSpiTransport, is_spi_transport\n"
            "fake = FakeSpiTransport(default=[0, 0])\n"
            "if not is_spi_transport(fake):\n"
            "    raise SystemExit('FakeSpiTransport is not a transport')\n"
            "if fake.transfer([0x0C, 43]) != [0, 0]:\n"
            "    raise SystemExit('no scripted frame was returned')\n"
            "fake.close()\n"
            "print('ok')\n"
        )
        self.assert_ran(result)


if __name__ == "__main__":
    unittest.main()
