#!/usr/bin/env python3

import logging.config
import sys
import argparse
from pathlib import Path

from ruamel.yaml import YAML

from logger.usb_meter import USBMeter
from logger.device import get_devices, devices_by_vid_pid, devices_by_serial_number
from file_stop_provider import FileStopProvider
from file_data_logger import OutputType


class Logger:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def _start_logging(self, args):
        log_file_name = args.logFile
        num_log_level = 50 - min(4, 2 + args.verbose) * 10
        log_level = logging.getLevelName(num_log_level)

        script = Path(__file__).resolve()
        folder = script.parent
        config = folder / 'logging.yaml'

        with open(config, "rt", encoding="UTF_8") as f:
            yaml = YAML(typ="safe")
            yaml_config = yaml.load(f)
            yaml_config['handlers']['console']['level'] = log_level
            if log_file_name:
                yaml_config['handlers']['file']['filename'] = log_file_name
                yaml_config['loggers']['root']['handlers'].append("file")
            else:
                del yaml_config['handlers']['file']
            logging.config.dictConfig(yaml_config)

    def _device_list(self, args):
        devices = get_devices()
        self._logger.info("Available devices:")
        for device in devices:
            sn = device.serial_number
            product = device.product_name
            manufacturer = device.manufacturer_name
            self._logger.info(f"- {device.device_info.vid:x}:{device.device_info.pid:x} {manufacturer} {product} (type: {device.device_info.model.name} SN: {sn})")

    def _get_id_description(self, args):
        if args.id:
            return "vid:pid = %s" % args.id
        if args.serial_number:
            return "serial number = %X" % args.serial_number
        raise RuntimeError("unknown id kind")

    def _split_id(self, id):
        tokens = id.split(":")
        return int(tokens[0], 16), int(tokens[1], 16)

    def _devices_by_id(self, args):
        if args.id:
            vid, pid = self._split_id(args.id)
            return devices_by_vid_pid(vid, pid)
        if args.serial_number:
            return devices_by_serial_number(args.serial_number)
        return None

    def _find_device(self, args):
        devices = self._devices_by_id(args)
        device = next(devices, None)
        if not device:
            raise RuntimeError("No devices found with: %s" % self._get_id_description(args))
        if next(devices, None):
            raise RuntimeError("Too many devices found with: %s" % self._get_id_description(args))
        return device

    def _device_show(self, args):
        device = self._find_device(args)
        self._logger.info(f"Vendor ID:     {device.device_info.vid:x}")
        self._logger.info(f"Product ID:    {device.device_info.pid:x}")
        self._logger.info(f"Type:          {device.device_info.model.name}")
        self._logger.info(f"Serial number: {device.serial_number}")

    def _log_data(self, args):
        device = self._find_device(args)
        stop_provider = FileStopProvider()
        meter = USBMeter(device=device, stop_provider=stop_provider, crc=not args.no_crc, alpha=args.alpha)
        meter.setup_device()
        meter.initialize_communication()
        output_type = OutputType[args.type.upper()]
        with output_type.clazz(args.output, args.latest_only) as data_logger:
            meter.run(data_logger)

    def main(self):
        parser = argparse.ArgumentParser(prog="um120_logger")
        default = ' (default: %(default)s)'
        parser.add_argument('-v', '--verbose', action='count', default=1, help="set the verbosity level" + default)
        parser.add_argument('-l', '--logFile', help="logfile name")
        subparsers = parser.add_subparsers(required=True, dest="subcommand", title='subcommands',
                                           description='valid subcommands', help='sub-command help')

        id_parser = argparse.ArgumentParser(add_help=False)
        id_group = id_parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument('--id', help="Device vendorid:productid")
        id_group.add_argument('--serial-number', type=lambda x: int(x, 16), help="Device serial number")

        parser_log = subparsers.add_parser('log', parents=[id_parser], help="log power data")
        parser_log.add_argument("--no-crc", action="store_true", help="Disable CRC checks")
        parser_log.add_argument("--alpha", type=float, default=0.9, help="Temperature EMA factor")
        parser_log.add_argument("-o", "--output", default="-", help="Output file, or '-' for stdout (default).")
        parser_log.add_argument('-t', '--type',
                            choices=[_type.type.lower() for _type in OutputType],
                            default=OutputType.CSV.name.lower(), help="Select output file type" + default)
        parser_log.add_argument("--latest-only", action="store_true", help="Only log the latest measurement per batch")
        parser_log.set_defaults(func=self._log_data)

        parser_device = subparsers.add_parser('device', help="device commands")
        device_subparsers = parser_device.add_subparsers(required=True, dest="subcommand", title='subcommands',
                                                         description='valid subcommands', help='sub-command help')
        parser_device_list = device_subparsers.add_parser('list', help="List devices")
        parser_device_list.set_defaults(func=self._device_list)
        parser_device_show = device_subparsers.add_parser('show', parents=[id_parser], help="Show device details")
        parser_device_show.set_defaults(func=self._device_show)

        args = parser.parse_args()

        self._start_logging(args)
        try:
            args.func(args)
            return 0
        except Exception as e:
            self._logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    logger = Logger()
    sys.exit(logger.main())
