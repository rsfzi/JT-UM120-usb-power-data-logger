from logger.measurement import MeasurementData


class DataLogger:
    def init(self) -> None:
        pass

    def log(self, data: MeasurementData) -> None:
        pass


class StreamDataLogger(DataLogger):
    def __init__(self, stream):
        self._stream = stream

    def init(self) -> None:
        self._stream.write("timestamp voltage_V current_A dp_V dn_V temp_C_ema energy_Ws capacity_As\n")

    def log(self, data: MeasurementData) -> None:
        self._stream.write(
            f"{data.timestamp:.3f} {data.voltage:7.5f} "
            f"{data.current:7.5f} {data.dp:5.3f} "
            f"{data.dn:5.3f} {data.temperature:6.3f} "
            f"{data.energy:.6f} {data.capacity:.6f}"
            "\n"
        )
