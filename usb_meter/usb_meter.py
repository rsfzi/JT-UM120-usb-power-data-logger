import logging
import time
from typing import Optional, Callable, List
import datetime

import crc
import usb.core
import usb.util

from .device import Device, DeviceModel
from .measurement import ElectricalMeasurement
from .stop_provider import StopProvider


class USBMeter:
    def __init__(self, device: Device, stop_provider: StopProvider, use_crc: bool = False, alpha: float = 0.9):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.use_crc = crc
        self.alpha = alpha
        self.energy = 0.0
        self.capacity = 0.0
        self.temp_ema = None
        self.crc_calculator = self._setup_crc() if use_crc else None
        self._device = device
        self._stop_provider = stop_provider
        self.ep_in = None
        self.ep_out = None

    def _setup_crc(self) -> Optional[Callable]:
        width = 8
        poly = 0x39
        init_value = 0x42
        final_xor_value = 0x00
        config = crc.Configuration(
            width, poly, init_value, final_xor_value,
            reverse_input=False, reverse_output=False
        )
        if hasattr(crc, "CrcCalculator"):
            return crc.CrcCalculator(config, use_table=True).calculate_checksum
        return crc.Calculator(config, optimized=True).checksum

    def setup_device(self) -> None:
        self._device.usb_device.reset()

        # Find and setup HID interface
        interface_num = self._find_hid_interface()
        if self._detach_kernel_driver(interface_num):
            #self._device.usb_device.set_configuration()
            pass

        # Configure device
        cfg = self._device.usb_device.get_active_configuration()
        intf = cfg[(interface_num, 0)]

        # Get endpoints
        self.ep_out = self._find_endpoint(intf, usb.util.ENDPOINT_OUT)
        self.ep_in = self._find_endpoint(intf, usb.util.ENDPOINT_IN)

    def _find_hid_interface(self) -> int:
        for cfg in self._device.usb_device:
            for interface in cfg:
                if interface.bInterfaceClass == 0x03:  # HID class
                    return interface.bInterfaceNumber
        raise RuntimeError("No HID interface found")

    def _detach_kernel_driver(self, interface_num: int) -> bool:
        if self._device.usb_device.is_kernel_driver_active(interface_num):
            try:
                self._device.usb_device.detach_kernel_driver(interface_num)
            except usb.core.USBError as e:
                raise RuntimeError(f"Could not detach kernel driver: {e}")
            return True
        return False

    def _find_endpoint(self, interface, direction) -> usb.core.Endpoint:
        return usb.util.find_descriptor(
            interface,
            custom_match=lambda e:
            usb.util.endpoint_direction(e.bEndpointAddress) == direction
        )

    def print_device_info(self) -> None:
        self._logger.debug("Device configuration %x:%x", self._device.device_info.vid, self._device.device_info.pid)
        for cfg in self._device.usb_device:
            self._logger.debug("Config %s", cfg.bConfigurationValue)
            for interface in cfg:
                self._logger.debug("  Interface %s", interface.bInterfaceNumber)
                for ep in interface:
                    self._logger.debug("    Endpoint %02x", ep.bEndpointAddress)

    def initialize_communication(self) -> None:
        init_sequence = [
            (b"\xaa\x81", b"\x8e"),
            (b"\xaa\x82", b"\x96"),
        ]

        if self._device.device_info.model in (DeviceModel.FNB58, DeviceModel.FNB48S):
            init_sequence.append((b"\xaa\x82", b"\x96"))
        else:
            init_sequence.append((b"\xaa\x83", b"\x9e"))

        for prefix, suffix in init_sequence:
            self.ep_out.write(prefix + b"\x00" * 61 + suffix)
            time.sleep(0.01)

    def decode_packet(self, data: bytes, timestamp: datetime.datetime) -> List[ElectricalMeasurement]:
        # Data is 64 bytes (64 bytes of HID data minus vendor constant 0xaa)
        # First byte is HID vendor constant 0xaa
        # Second byte is payload type:
        #    0x04 is data packet
        #    Other types (0x03 and maybe other ones) is unknown
        # Next 4 samples each 15 bytes. 60 bytes total.
        # At the end 2 bytes:
        #   1 byte is semi constant with unknown purpose.
        #   1 byte (last) is a 8-bit CRC checksum

        if data[1] != 0x04:  # Not a data packet
            return []

        if self.use_crc and self.crc_calculator:
            if not self._verify_crc(data):
                return []

        measurements = []
        sample_delta = datetime.timedelta(milliseconds=10)
        base_time = timestamp - 4 * sample_delta    # 4 samples, 10ms each

        for i in range(4):
            offset = 2 + 15 * i
            measurement_time = base_time + i * sample_delta
            measurement = self._decode_measurement(data[offset:offset + 15], measurement_time)
            measurements.append(measurement)

        return measurements

    def _decode_measurement(self, data: bytes, timestamp: datetime.datetime) -> ElectricalMeasurement:
        voltage = int.from_bytes(data[0:4], 'little') / 100000
        current = int.from_bytes(data[4:8], 'little') / 100000
        dp = int.from_bytes(data[8:10], 'little') / 1000
        dn = int.from_bytes(data[10:12], 'little') / 1000
        temp_celsius = int.from_bytes(data[13:15], 'little') / 10.0

        # Update running totals
        power = voltage * current
        self.energy += power * 0.01  # 10ms interval
        self.capacity += current * 0.01

        # Update EMA temperature
        if self.temp_ema is None:
            self.temp_ema = temp_celsius
        else:
            self.temp_ema = temp_celsius * (1.0 - self.alpha) + self.temp_ema * self.alpha

        return ElectricalMeasurement(
            device=self._device,
            timestamp=timestamp,
            voltage=voltage,
            current=current,
            dp=dp,
            dn=dn,
            temperature=self.temp_ema,
            energy=self.energy,
            capacity=self.capacity
        )

    def _verify_crc(self, data: bytes) -> bool:
        actual = data[-1]
        expected = self.crc_calculator(bytearray(data[1:-1]))
        if actual != expected:
            self._logger.warning("CRC mismatch: expected %02x, got %02x", expected, actual)
            return False
        return True

    def _do_log(self, data_logger):
        next_refresh = datetime.datetime.now() + self._device.device_info.refresh_rate
        while True:
            data = self.ep_in.read(64, timeout=5000)
            now = datetime.datetime.now(datetime.timezone.utc)
            measurements = self.decode_packet(data, now)
            if measurements:
                data_logger.log(measurements)

            if datetime.datetime.now() >= next_refresh:
                next_refresh = datetime.datetime.now() + self._device.device_info.refresh_rate
                self.ep_out.write(b"\xaa\x83" + b"\x00" * 61 + b"\x9e")

            if self._stop_provider.should_stop():
                break

    def run(self, data_logger) -> None:
        self._logger.debug("log with CRC: %s", self.use_crc)
        try:
            self._do_log(data_logger)
        except KeyboardInterrupt:
            self._logger.info("Keyboard interrupt received -> stopping...")

        self._drain_buffer()

    def _drain_buffer(self) -> None:
        self._logger.debug("Draining USB buffer...")
        try:
            while True:
                data = self.ep_in.read(64, timeout=1000)
                if data:
                    self._logger.debug("Drained %d bytes", len(data))
        except usb.core.USBTimeoutError:
            self._logger.debug("Buffer drain complete")
