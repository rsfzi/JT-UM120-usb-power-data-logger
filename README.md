[![Pylint](https://github.com/rsfzi/JT-UM120-usb-power-data-logger/actions/workflows/pylint.yml/badge.svg)](https://github.com/rsfzi/JT-UM120-usb-power-data-logger/actions/workflows/pylint.yml)

Fork of [fnirsi-usb-power-data-logger](https://github.com/baryluk/fnirsi-usb-power-data-logger)

Data logger for JT-UM120, FNIRSI FNB48, FNIRSI C1 and FNIRSI FNB58 USB power meters
------------------------------------------------------------

FNIRSI FNB48, FNIRSI C1, FNIRSI FNB58 are cheap and relatively good USB
power meters, supporting various charging protocols, voltages, and
additionally PC communication.

This is a result of reverse engineering of FNB-48 protocol over lazy
Saturday.


Requirements
------------

Linux. (It might work on non-linux systems too, but untested)

Python 3.12 or newer.

Installation
------------

```shell
python3 -m venv venv
venv/bin/pip install usb-multimeter
```

Running under normal user (non-root)
------------------------------------

Above examples showed running with sudo (root user). This is because
these USB devices are of HID type, and not standard serial devices. You
can manually change permissions of them with something similar to `sudo
chown $USER /dev/bus/usb/001/030`, or better yet, install `udev` rules as
described below.

Create USB group:
```shell
sudo addgroup usbmeter
```

Install udev rules:

```shell
sudo install --mode=0644 --target-directory=/etc/udev/rules.d/ venv/lib/python3.12/site-packages/usb_multimeter/udev/90-usb-power-meter.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

This should make `fnirsi_logger.py` work for users of the usbmeter group.


Accuracy / resolution
---------------------

Time - few ms. By default samples every 10ms (technically 4 samples every
40ms). Time is printed as UNIX epoch in seconds, with 1ms resolution.

Voltage, current - all printed decimal digits. 0.00001 unit.

Temperature - device resolution is 0.1°C, but a low pass filter is used
to smooth it a bit, and output with 0.01°C. Less than a second delay
expected. As far as I can tell negative values for temperature are not
supported, it will report close to 0°C. Temperatures in range 0–70°C were
tested.

Energy and capacity - all printed decimal digits. Note: Device does not
send energy and capacity. Values are integrated (from power and current)
on the host instead. They do start at zero at program startup.

Note: It is expected voltage are positive, if not Energy and Capacity
might go backwards!

Note: Power is not provided in the output. Just multiply voltage and
current values to get power in Watts.


Supported devices
-----------------

FNIRSI FNB48 and FNIRSI C1 are known to work. It will use first that it
finds.

FNIRSI FNB58 is also known to work, thanks to work of @didim99.

FNIRSI FNB48S should also work.

JT-UM120 are known to work.

Make sure to have relatively recent firmware. My FNIRSI C-1 came with
very old firmware (0.20) that did not work out of the box, but upgrading
to the latest firmware (0.70) made everything work with exactly same
code.


Built-in storage
----------------

Some meters do have small FAT partition that a metter can log to, and
then read back on a computer as a simple storage device. A format is
simple binary format called CFN. There is a tool at
https://github.com/didim99/usbmeter-utils to read it and convert to CSV.

Data analysis
-------------

You can do whatever you want, it just simple text data that can be feed
to file or a pipe. Import to program, spreadsheet, Python, R, Octave,
gnuplot, export to InfluxDB, Prometheus, Kafka, MQTT. For quick and dirty
work, one can use `awk`, `sort`, or my command-line program
[kolumny](https://github.com/baryluk/kolumny). There are no limits.

Limitation
----------

All values seems to be correct. No extra calibration curves are used, as
device sends values that already have device calibration applied.

Program uses fixed sampling rate of 100 samples per second (highest
avilable). If you want lower sampling rate, just skip some output lines.
In gnuplot to speed up very long (days) logs, use `every 10` for example,
to skip lines automatically. If you really need lower sample rate, open a
GitHub Issue about it. For now you can use something like
`./fnirsi_logger.py | awk 'BEGIN {next_t=0.0;} { if ($1 >= next_t) { print $0; next_t = $1 + 1.0;} }'`
to limit output to 1 sample per second.

TODO
----

FNB48: Sometimes on program exit, the power meter display gets frozen.

Note: This is now partially fixed (when we exit, we make sure to read all
the data before actually exiting - this way power meter does not fill up
its internal FIFO buffers, and block forever). Partially, because
sometimes meter still gets stuck. Waiting a bit, and reruning script few
times, sometimes bring the device back to life. If everything fails,
replug the device to reinitialize it.

It might make sense to add triggers (configured via command line
options): when to start outputing data (i.e. when current goes from low
to above 20mA), and when to stop outputing data and exit (i.e. when
current goes back to below 10mA for 60 consequtive seconds). It is easy
to add, I just do not have much use for it personally.

Power Delivery type detection does not work.

Firmware update still requires Windows. Running in qemu / virt-manager,
and doing USB redirect works for this purposes. Unlikely to be
implemented.

