#!/usr/bin/env python3

import logging.config
import sys
from typing import Optional
from typing import Union, IO
import argparse
from pathlib import Path
from contextlib import contextmanager

from ruamel.yaml import YAML

from data_logger import StreamDataLogger
from usb_meter import USBMeter
from device import get_devices

@contextmanager
def open_or_stdout(path: Optional[Union[str, Path, IO[str]]] = None,
                   mode: str = "w",
                   encoding: str = "utf-8"):
    """
    Context manager that yields a text file-like object.
    - path can be None or '-' to mean stdout.
    - path can be an already-open file-like object (has write()).
    """
    # If user passed an open file-like object, just use it
    if hasattr(path, "write"):
        yield path
        return

    # stdout convention
    if path is None or path == "-":
        yield sys.stdout
        return

    # Otherwise open a file path
    p = Path(path)
    with p.open(mode=mode, encoding=encoding) as f:
        yield f

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
        for device in devices:
            self._logger.info(f"Found device: {device.device_info.model.name}")

    def _log_data(self, args):
        devices = get_devices()
        if not devices:
            raise RuntimeError("No supported USB meter found")
        device = devices[0]
        meter = USBMeter(device=device, crc=args.crc, alpha=args.alpha)
        meter.setup_device()
        meter.initialize_communication()
        with open_or_stdout(args.output) as out:
            data_logger = StreamDataLogger(out)
            data_logger.init()
            meter.run(data_logger)

    def main(self):
        parser = argparse.ArgumentParser()
        default = ' (default: %(default)s)'
        parser.add_argument('-v', '--verbose', action='count', default=1, help="set the verbosity level" + default)
        parser.add_argument('-l', '--logFile', help="logfile name")
        subparsers = parser.add_subparsers(required=True, dest="subcommand", title='subcommands',
                                           description='valid subcommands', help='sub-command help')
        parser_log = subparsers.add_parser('log', help="log power data")
        parser_log.add_argument("--crc", action="store_true", help="Enable CRC checks")
        parser_log.add_argument("--alpha", type=float, default=0.9, help="Temperature EMA factor")
        parser_log.add_argument("-o", "--output", default="-", help="Output file path, or '-' for stdout (default).")
        parser_log.set_defaults(func=self._log_data)

        parser_device = subparsers.add_parser('device', help="device commands")
        device_subparsers = parser_device.add_subparsers(required=True, dest="subcommand", title='subcommands',
                                                         description='valid subcommands', help='sub-command help')
        parser_device_list = device_subparsers.add_parser('list', help="list devices")
        parser_device_list.set_defaults(func=self._device_list)

        args = parser.parse_args()

        self._start_logging(args)
        try:
            args.func(args)
            return 0
        except Exception as e:
            self._logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    logger = Logger()
    sys.exit(logger.main())
