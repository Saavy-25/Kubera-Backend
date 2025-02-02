if __name__ == "__main__":
    try:
        with open("config.ini", "x") as f:
            f.write("[AzureDocInteli]\nresource_key=")
    except FileExistsError:
        print("config.ini exists")