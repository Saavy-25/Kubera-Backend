if __name__ == "__main__":
    try:
        with open(".env", "x") as f:
            f.write("MONGO_URI=\n")
            f.write("AZURE_RESOURCE_KEY=\n")
            f.write("DECODE_PROMPT=\n")
            f.write("MAP_PROMPT=")
    except FileExistsError:
        print(".env exists")