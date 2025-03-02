if __name__ == "__main__":
    try:
        with open(".env", "x") as f:
            f.write("MONGO_URI=\n")
            f.write("AZURE_RESOURCE_KEY=")

    except FileExistsError:
        print(".env exists")