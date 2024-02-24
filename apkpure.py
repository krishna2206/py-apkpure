import cloudscraper

from appsearch import AppSearch
from app import App


class Apkpure:
    def __init__(self) -> None:
        self.__scraper = cloudscraper.create_scraper()

    @staticmethod
    def search_app(query):
        appsearch = AppSearch(query)
        return appsearch.results

    def get_app(self, app_url, as_dict=False):
        app = App(app_url, scraper=self.__scraper)

        if as_dict:
            return app.as_dict()
        return app