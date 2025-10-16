from fastapi import FastAPI
import uvicorn

from .device_handler import DeviceHandler, DeviceItem


app = FastAPI()
device_handler = DeviceHandler()


@app.get("/")
def hello_world():
    return {"Hello": "World"}


@app.get("/devices/")
def get_devices() -> list[DeviceItem]:
    devices = device_handler.list_devices()
    return devices


def server_main(args) -> None:
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info", reload=False)
