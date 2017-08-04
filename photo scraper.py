import urllib.request


def url_gen(id):
    return "https://platform-static-files.s3.amazonaws.com/premierleague/photos/players/110x140/p" + str(id) + ".png"

def main():
    dest_folder = "D:\\Coding\\Fantasy Football photos\\Photos\\"


    urllib.request.urlretrieve("https://platform-static-files.s3.amazonaws.com/premierleague/photos/players/110x140/p57248.png", dest_folder+"p57248.png")


if __name__ == "__main__":
    main()