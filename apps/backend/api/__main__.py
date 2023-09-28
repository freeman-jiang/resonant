if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", '8000'))

    uvicorn.run('api.main:app', host=host, port=port, reload=True)
