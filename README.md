# scietex.hal.spi

SPI transport backends shared by the `scietex.hal.*` device distributions.

A transport is the narrow seam between a device driver and the bus. Devices
send whole frames through `transfer()` and release the bus with `close()`, so
the same driver works over `spidev`, over gpiozero's hardware SPI, or over a
scripted fake in tests. The package ships no device code and has no runtime
dependencies: the optional backends are imported only when they are used.

## The protocol

```python
class SpiTransport(Protocol):
    def transfer(self, tx: Sequence[int]) -> list[int]: ...
    def close(self) -> None: ...
```

* `transfer(tx)` sends one frame of words in `0..255` and returns the received
  words in the same order.
* `close()` releases the bus handle; repeated calls have no effect. If the
  underlying close fails, the transport stays open and `close()` can be
  retried.
* `closed` is `True` once `close()` has run. For a transport that wraps a
  caller-supplied handle, it reports that the transport itself is closed, not
  that the shared bus was closed.

Any object with callable `transfer` and `close` methods is accepted. Use
`is_spi_transport(obj)` for the check: unlike `isinstance(obj, SpiTransport)`,
it rejects class objects. Use `SpiTransport` for typing only.

Failures raise `TransportError`, which subclasses `OSError` so callers that
already handle spidev or gpiozero I/O errors keep working. A transaction
attempted after close raises `TransportClosed`, a `TransportError` subclass.

## Backends

| Transport | Install | Notes |
| --- | --- | --- |
| `SpiDevTransport` | `pip install 'scietex.hal.spi[spi]'` | Default. Opens `/dev/spidev<bus>.<device>` through `spidev`, Linux only. |
| `GpiozeroSpiTransport` | `pip install 'scietex.hal.spi[gpiozero]'` | Wraps a gpiozero hardware SPI object. Resolved lazily as `scietex.hal.spi.GpiozeroSpiTransport`. |
| `FakeSpiTransport` | none | In-memory backend with scripted responses, for tests without hardware. |

```python
from scietex.hal.spi import SpiDevTransport

transport = SpiDevTransport(bus=0, device=0, max_speed_hz=500_000)
transport.transfer([0x00, 43])
transport.close()
```

`SpiDevTransport` transfers with `xfer2`, which keeps chip select asserted for
the whole frame; `xfer` would deassert it between 8-bit words.

`GpiozeroSpiTransport` builds a private shared gpiozero `SPIDevice` by default,
or wraps one supplied with `spi=`. On a Raspberry Pi it also patches gpiozero so
two hardware-SPI devices can share one port when they use different chip-select
lines (`fix_gpiozero_dual_cs_spi`, also exported for callers that build their
own gpiozero devices). Without the RPi pin backend the patch is a no-op.

A bare install ships no hardware backend; constructing one raises `ImportError`
naming the extra to install.

## Default selection

`build_default_transport` maps the legacy device keywords onto a backend:

| Keyword | `SpiDevTransport` | `GpiozeroSpiTransport` |
| --- | --- | --- |
| `port` | `bus` | `port` |
| `device` | `device` | `device` |
| `clock_pin`, `mosi_pin`, `miso_pin`, `select_pin` | selects the gpiozero backend | forwarded as-is |

```python
from scietex.hal.spi import build_default_transport

build_default_transport(port=0, device=1)  # SpiDevTransport(bus=0, device=1)
build_default_transport(clock_pin=11, mosi_pin=10)  # GpiozeroSpiTransport(...)
```

Any pin keyword selects the gpiozero backend and requires the `gpiozero`
extra; without pin keywords the spidev backend is built with `port or 0` and
`device or 0`. `port` and `device` are accepted by both backends and are simply
forwarded.

The selector takes backend keywords only. Conflict rejection — passing backend
keywords together with `transport=` or `spi=` — is the responsibility of each
device constructor, which owns that argument surface; the selector itself raises
`TypeError` when given a `transport=` keyword.

## Ownership

Create one transport per device; all channels of a device share it. The device's
`close()` delegates to its transport.

* `SpiDevTransport` always owns and closes its spidev handle.
* `GpiozeroSpiTransport` closes only a handle it built. When it wraps a
  caller-supplied `spi=` object, `close()` marks the transport closed but leaves
  the shared bus open for its other users; the supplied handle's owner must
  outlive the wrapper and close it. Once that owner closes the handle, transfers
  through the wrapper raise `TransportClosed`.
* `FakeSpiTransport` only flips its `closed` flag.

## Linux permissions

`SpiDevTransport` needs the kernel SPI device node and permission to open it.
Enable kernel SPI first, for example with `dtparam=spi=on` in
`/boot/firmware/config.txt` on current Raspberry Pi OS (the older path is
`/boot/config.txt`).

If the node exists but opening fails, add a udev rule. The development setup for
these packages uses the `gpio` group; adjust the group to match your system::

    SUBSYSTEM=="spidev", GROUP="gpio", MODE="0660"

Install the rule under `/etc/udev/rules.d/`, reload the rules, and reconnect the
device. The user running the process must be a member of the group named in the
rule; on Fedora setups that group is `gpio`, because no `spi` group exists.

## License

This project is licensed under the **MIT License** - see the LICENSE file for details.
