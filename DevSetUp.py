if __name__ == "__main__":
    try:
        with open(".env", "x") as f:
            f.write("MONGO_URI=\n")
            f.write("AZURE_RESOURCE_KEY=")

        with open("Dockerfile", "x") as f:
            f.write("FROM python:3.9-slim\n")
            f.write("WORKDIR /app\n")
            f.write("COPY . /app\n")
            f.write("RUN pip install --no-cache-dir -r requirements.txt\n")
            f.write("EXPOSE 8080\n")
            f.write("RUN --mount=type=secret,id=_env,dst=.env cat .env\n")
            f.write("CMD [\"python\", \"app.py\"]\n")

    except FileExistsError:
        print(".env exists")