import cloudscraper
from bs4 import BeautifulSoup

from helpers import Helpers


URL = "https://apkpure.fr"


class AppSearch:
    def __init__(self, query, lang="fr") -> None:
        self.__query = query
        self.__lang = lang
        self.results = {}
        self.__scraper = cloudscraper.create_scraper()
        self.__scraper.user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0"
        self.__get_results()

    def __get_results(self):
        html_content = self.__fetch_results(self.__query)
        self.results = self.__parse_results(html_content)

    def __fetch_results(self, query):
        response = self.__scraper.get(
            URL + f"/{self.__lang}/search",
            params={"q": query, "t": "app"}
        )
        if response.status_code == 200:
            return response.text
        raise Exception(f"Failed to fetch HTML content. {response.status_code} {response.reason}")

    def __parse_results(self, html_content):
        soup = BeautifulSoup(html_content, features="lxml")

        results = {"limit": 0, "results": []}
        no_result_block = soup.find("div", class_="list-title not-find-result")
        if no_result_block:
            return results

        # Locate the main search result container
        main_search_block = soup.find("div", class_="search-result-page search-app")

        # Parse brand or first APK info (if available)
        brand_or_first_apk_result = self.__parse_brand_or_first_apk(main_search_block)

        # Get total number of results
        total_results_text = soup.find("div", class_="list-title lighter sa-all-div sa-apps-div").find("span").text
        total_results = int(total_results_text)
        results["limit"] = total_results

        # Extract app results from the current page
        app_results_container = self.__find_app_results_container(main_search_block)
        for app_block in app_results_container.findAll("li"):
            result = self.__parse_app_result(app_block)
            results["results"].append(result)

        # Loop through pages to get all results (if needed)
        begin = 10  # Starting index for the next page
        while begin < total_results:
            print("Fetching next page...")
            page_url = URL + f"/fr/search-page?q={self.__query}&t=app&begin={begin}"
            response = self.__scraper.get(page_url)
            page_soup = BeautifulSoup(response.text, features="lxml")
            for app_block in page_soup.findAll("li"):
                result = self.__parse_app_result(app_block)
                results["results"].append(result)
            begin += 10

        # Add brand or first APK info as the first result (if available)
        if brand_or_first_apk_result:
            results["results"].insert(0, brand_or_first_apk_result)

        return results

    def __parse_brand_or_first_apk(self, main_search_block):
        """Parses brand info or first APK info if available."""
        brand_info_block = main_search_block.find("div", class_="first brand is-brand sa-all-div sa-apps-div mb")
        first_apk_block = main_search_block.find("div", class_="first first-apk sa-all-div sa-apps-div mb")

        if brand_info_block:
            # Parse brand info with multiple icon resolutions
            brand_icon_url = brand_info_block.find("img", class_="icon")["src"]
            return {
                "name": brand_info_block.find("p", class_="p1").text.strip(),
                "developer": brand_info_block.find("p", class_="p2").text.strip(),
                "icon": {
                    "128": Helpers.set_icon_res(brand_icon_url, res=128),
                    "256": Helpers.set_icon_res(brand_icon_url, res=256),
                    "512": Helpers.set_icon_res(brand_icon_url, res=512),
                },
                "url": URL + brand_info_block.find("a", class_="first-info brand-info")["href"],
            }
        elif first_apk_block:
            # Parse first apk info with multiple icon resolutions
            first_apk_icon_url = first_apk_block.find("img", class_="first-info-img")["src"]
            return {
                "name": first_apk_block.find("p", class_="p1").text.strip(),
                "developer": first_apk_block.find("p", class_="p2").text.strip(),
                "icon": {
                    "128": Helpers.set_icon_res(first_apk_icon_url, res=128),
                    "256": Helpers.set_icon_res(first_apk_icon_url, res=256),
                    "512": Helpers.set_icon_res(first_apk_icon_url, res=512),
                },
                "url": URL + first_apk_block.find("a", class_="first-info")["href"],
            }
        else:
            return None

    def __find_app_results_container(self, main_search_block):
        """Finds the container holding individual app results."""
        app_results_container = main_search_block.find(
            "div", class_="list sa-all-div app-list"
        )
        if app_results_container is None:
            app_results_container = main_search_block.find(
                "div", class_="list sa-apps-div show-top-stroke app-list"
            )
        return app_results_container

    def __parse_app_result(self, app_block):
        """Parses and returns a single app result dictionary."""
        return {
            "name": app_block.find("p", class_="p1").text.replace("\n", "").strip(),
            "developer": app_block.find("p", class_="p2")
            .text.replace("\n", "")
            .strip(),
            "tags": [
                tag.text
                for tag in app_block.find("div", class_="tags").findAll(
                    "span", class_="tag"
                )
            ],
            "icon": {
                "128": Helpers.set_icon_res(
                    app_block.find("div", class_="l").find("img")["src"], res=128
                ),
                "256": Helpers.set_icon_res(
                    app_block.find("div", class_="l").find("img")["src"], res=256
                ),
                "512": Helpers.set_icon_res(
                    app_block.find("div", class_="l").find("img")["src"], res=512
                ),
            },
            "url": URL + app_block.find("a", class_="dd")["href"],
        }
