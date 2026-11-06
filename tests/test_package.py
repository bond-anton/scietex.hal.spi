"""Test the distributive's public surface."""

import unittest

import scietex.hal.spi as spi
import scietex.hal.spi.gpiozero_helpers as gpiozero_helpers

EXPECTED_ALL = [
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


class TestPackage(unittest.TestCase):
    """The distributive imports and exposes the documented names."""

    def test_public_names_are_reachable(self) -> None:
        """The helper and the protocol gate are importable from the package."""
        self.assertTrue(callable(spi.fix_gpiozero_dual_cs_spi))
        self.assertTrue(callable(spi.is_spi_transport))

    def test_all_matches_the_documented_surface(self) -> None:
        """A star import yields exactly the documented names."""
        self.assertEqual(spi.__all__, EXPECTED_ALL)

    def test_all_names_resolve(self) -> None:
        """Every exported name resolves on a core install."""
        for name in spi.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(spi, name))

    def test_lazy_transport_stays_out_of_all(self) -> None:
        """The optional gpiozero transport is resolved lazily, not exported."""
        self.assertNotIn("GpiozeroSpiTransport", spi.__all__)
        self.assertIn("GpiozeroSpiTransport", dir(spi))

    def test_helper_module_is_public(self) -> None:
        """gpiozero_helpers is importable under its public name."""
        self.assertIs(
            gpiozero_helpers.fix_gpiozero_dual_cs_spi,
            spi.fix_gpiozero_dual_cs_spi,
        )
        self.assertEqual(gpiozero_helpers.__all__, ["fix_gpiozero_dual_cs_spi"])


if __name__ == "__main__":
    unittest.main()
