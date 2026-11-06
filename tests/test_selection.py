"""Tests for the default SPI backend selection."""

import sys
import types
import unittest
from unittest import mock

from scietex.hal.spi import (
    GPIOZERO_PIN_ARGS,
    GPIOZERO_SPI_ARGS,
    build_default_transport,
    spidev_spi,
)

GPIOZERO_BACKEND = "scietex.hal.spi.gpiozero_spi"


class _RecordingGpiozeroTransport:
    """Stand-in for GpiozeroSpiTransport that records its keywords."""

    instances = []

    def __init__(self, **spi_args):
        self.spi_args = spi_args
        _RecordingGpiozeroTransport.instances.append(self)


def _fake_gpiozero_module():
    """Build a stand-in for the gpiozero backend module."""
    module = types.ModuleType(GPIOZERO_BACKEND)
    module.GpiozeroSpiTransport = _RecordingGpiozeroTransport
    return module


class TestBuildDefaultTransport(unittest.TestCase):
    """
    Testing which backend the default selector builds.
    """

    def setUp(self) -> None:
        _RecordingGpiozeroTransport.instances = []

    def test_pin_keyword_selects_gpiozero_backend(self) -> None:
        """
        A pin keyword builds the gpiozero backend with that keyword.
        """
        with mock.patch.dict(sys.modules, {GPIOZERO_BACKEND: _fake_gpiozero_module()}):
            transport = build_default_transport(clock_pin=11)
        self.assertIs(transport, _RecordingGpiozeroTransport.instances[0])
        self.assertEqual(transport.spi_args, {"clock_pin": 11})

    def test_every_pin_keyword_selects_gpiozero_backend(self) -> None:
        """
        Each pin keyword alone is enough to select the gpiozero backend.
        """
        expected = {
            "clock_pin": 11,
            "mosi_pin": 10,
            "miso_pin": 9,
            "select_pin": 8,
        }
        for name in GPIOZERO_PIN_ARGS:
            with self.subTest(keyword=name):
                _RecordingGpiozeroTransport.instances = []
                with mock.patch.dict(
                    sys.modules, {GPIOZERO_BACKEND: _fake_gpiozero_module()}
                ):
                    transport = build_default_transport(**{name: expected[name]})
                self.assertEqual(transport.spi_args, {name: expected[name]})

    def test_port_and_device_are_forwarded_to_the_pin_backend(self) -> None:
        """
        port and device belong to both backends and reach the gpiozero one.
        """
        with mock.patch.dict(sys.modules, {GPIOZERO_BACKEND: _fake_gpiozero_module()}):
            transport = build_default_transport(port=1, device=2, clock_pin=11)
        self.assertEqual(transport.spi_args, {"port": 1, "device": 2, "clock_pin": 11})

    def test_none_keywords_are_not_forwarded(self) -> None:
        """
        Keywords left at None never reach the backend constructor.
        """
        with mock.patch.dict(sys.modules, {GPIOZERO_BACKEND: _fake_gpiozero_module()}):
            transport = build_default_transport(clock_pin=11, mosi_pin=None)
        self.assertEqual(transport.spi_args, {"clock_pin": 11})

    def test_no_pin_keyword_selects_spidev_with_port_and_device(self) -> None:
        """
        port and device alone map to bus and device on the spidev backend.
        """
        with mock.patch.object(spidev_spi, "SpiDevTransport") as constructor:
            transport = build_default_transport(port=1, device=2)
        constructor.assert_called_once_with(bus=1, device=2)
        self.assertIs(transport, constructor.return_value)

    def test_no_keywords_select_spidev_defaults(self) -> None:
        """
        Without keywords the spidev backend opens bus 0, device 0.
        """
        with mock.patch.object(spidev_spi, "SpiDevTransport") as constructor:
            build_default_transport()
        constructor.assert_called_once_with(bus=0, device=0)

    def test_missing_gpiozero_names_the_gpiozero_extra(self) -> None:
        """
        A pin keyword without gpiozero raises ImportError naming the extra.
        """
        saved_backend = sys.modules.pop(GPIOZERO_BACKEND, None)
        try:
            with (
                mock.patch.dict(sys.modules, {"gpiozero": None}),
                self.assertRaises(ImportError) as context,
            ):
                build_default_transport(clock_pin=11)
        finally:
            if saved_backend is not None:
                sys.modules[GPIOZERO_BACKEND] = saved_backend
        self.assertIn("scietex.hal.spi[gpiozero]", str(context.exception))

    def test_transport_keyword_is_rejected(self) -> None:
        """
        The selector takes backend keywords only; conflict checking with an
        injected transport belongs to the device constructors.
        """
        with self.assertRaises(TypeError):
            build_default_transport(transport=object())

    def test_pin_keywords_are_a_subset_of_the_backend_keywords(self) -> None:
        """
        Every pin keyword is also accepted by the gpiozero backend.
        """
        self.assertLessEqual(set(GPIOZERO_PIN_ARGS), set(GPIOZERO_SPI_ARGS))


if __name__ == "__main__":
    unittest.main()
