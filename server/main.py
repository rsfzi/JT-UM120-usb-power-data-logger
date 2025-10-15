from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def hello_world():
    return {"Hello": "World"}


def server_main(args) -> None:
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info", reload=False)
