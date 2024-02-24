from appsearch import AppSearch
from app import App


if __name__ == "__main__":
    # appsearch = AppSearch("poe")
    # print(appsearch.results)

    #? Parse using method 1
    # app = App("https://apkpure.fr/fr/facebook-lite/com.facebook.lite").as_dict()
    # print(app)
    # app.get("download")()

    #? Parse using method 2
    app = App("https://apkpure.fr/fr/forex-trading-for-beginners/com.tiim.goforexx24").as_dict()
    print(app)
    # app.get("download")()

    pass