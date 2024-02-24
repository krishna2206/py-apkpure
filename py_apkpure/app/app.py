import os
import shutil
from functools import partial

import cloudscraper
from tqdm import tqdm
from bs4 import BeautifulSoup

from py_apkpure.helpers import Helpers


class App:
    """
    Represents a Apkpure application.
    Use as_dict() method to get members.

    Members:
        name (str) : the name of the application.
        version (str) : the version of the application.
        developer (str) : the developer of the application.
        icon (str) : the url of the application's icon.
        size (float) : the size of the application in bytes.
        rating (float) : the average rating of the application.
        screenshots (list) : list of the application's screenshots.
        description (str) : long description of the application.
        tags (list) : list of the application's tags.
        download (function) : built-in function to download the app

    Built-in app downloader function arguments:
        output_dir (str) : the output directory. Defaults to the current working directory.
        output_filename (str) : the output file name. Defaults to the name provided by Apkpure
        progress_bar (bool) : show or not the progession bar. Defaults to True.
    """
    def __init__(self, app_url, **kwargs) -> None:
        self.__app_url = app_url

        if kwargs.get("scraper") is not None:
            self.__scraper = kwargs.get("scraper")
        else:
            self.__scraper = cloudscraper.create_scraper()
        self.__scraper.user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0"

        self.__init_app_data()

    def as_dict(self):
        return self.__dict__

    def __init_app_data(self):
        html_content = self.__fetch_app_page(self.__app_url)
        try:
            app_data = self.__parse_app_page(html_content)
        except Exception as error:
            print("Failed to parse. Falling back to parse method 2.")
            try:
                app_data = self.__parse_app_page_fallback(html_content)
            except Exception as error:
                raise error
            else:
                for key, value in app_data.items():
                    self.__dict__[key] = value
        else:
            for key, value in app_data.items():
                self.__dict__[key] = value

    def __fetch_app_page(self, app_url):
        response = self.__scraper.get(app_url)

        if response.status_code == 200:
            return response.text
        raise Exception(f"Failed to fetch HTML content. {response.status_code} {response.reason}")

    #? Parse method 1
    def __parse_app_page(self, html_content):
        soup = BeautifulSoup(html_content, features="lxml")
        app_data = {}

        #? Parse from details in top
        detail_top = soup.find("div", class_="detail_top")

        #! print(detail_top)

        app_data["icon"] = {
            "128": Helpers.set_icon_res(detail_top.find("div", class_="apk_info").find("img")["srcset"].replace(" 2x", ""), res=128),
            "256": Helpers.set_icon_res(detail_top.find("div", class_="apk_info").find("img")["srcset"].replace(" 2x", ""), res=128),
            "512": Helpers.set_icon_res(detail_top.find("div", class_="apk_info").find("img")["srcset"].replace(" 2x", ""), res=128)
        }
        app_data["name"] = detail_top.find("div", class_="title_link").find("h1").text
        app_data["version"] = detail_top.find(
            "p", class_="details_sdk").find("span").text.strip()
        app_data["developer"] = Helpers.clean_value(detail_top.find(
            "p", class_="details_sdk").find("span", attrs={"class": "developer"}).text)
        
        download_button = detail_top.find("a", class_="download_apk_news da")
        if not download_button:
            download_button = detail_top.find("a", class_="download_apk_news da no-right-radius")

        app_data["size"] = float(download_button["data-dt-file_size"])
        app_data["package_name"] = download_button["data-dt-package_name"]
        try:
            app_data["rating"] = float(detail_top.find("span", attrs={"itemprop": "ratingValue"}).text)
        except AttributeError:
            app_data["rating"] = None

        #? Parse description
        above_info = soup.find("div", class_="above-info")
        app_data["description"] = Helpers.clean_value(above_info.find("div", attrs={"class": "content"}).text)

        #? Parse screenshots block
        screen_box = soup.find("div", class_="screenbox")
        app_data["screenshots"] = [img["src"] for img in screen_box.find("div", id="screen").findAll("img")]

        #? Parse tag block
        tag_box = soup.find("div", class_="tag-box")
        app_data["tags"] = [Helpers.clean_value(span.text) for span in tag_box.findAll("span", class_="tag-item")]

        #? Parse download link
        version_link = None
        version_link = download_button["href"]

        if version_link is None:
            app_data["download"] = None
            app_data["playstore_only"] = True
        else:
            app_data["download"] = partial(
                self.__download,
                version_link)
            app_data["playstore_only"] = False

        return app_data

    # ! Parse method 2 (OUTDATED)
    def __parse_app_page_fallback(self, html_content):
        soup = BeautifulSoup(html_content, features="lxml")
        app_data = {}

        main_dl = soup.find("dl", class_="ny-dl ny-dl-n")

        app_data["icon"] = {
            "128": Helpers.set_icon_res(main_dl.find("div", class_="icon").find("img")["srcset"].replace(" 2x", ""), res=128),
            "256": Helpers.set_icon_res(main_dl.find("div", class_="icon").find("img")["srcset"].replace(" 2x", ""), res=128),
            "512": Helpers.set_icon_res(main_dl.find("div", class_="icon").find("img")["srcset"].replace(" 2x", ""), res=128)
        }
        app_data["name"] = main_dl.find("div", class_="title-like").find("h1").text
        app_data["version"] = main_dl.find(
            "div", class_="details-sdk").find("span", attrs={"itemprop": "version"}).text.strip()
        app_data["developer"] = main_dl.find(
            "div", class_="details-author").find("p", attrs={"itemprop": "publisher"}).text.replace("\n", "")
        app_data["size"] = float(main_dl.find("div", id="down_btns")["data-dt-filesize"])
        app_data["package_name"] = main_dl.find("div", id="down_btns")["data-dt-app"]
        try:
            app_data["rating"] = float(
                main_dl.find("div", class_="details-rating").find("span", attrs={"itemprop": "ratingValue"}).text)
        except AttributeError:
            app_data["rating"] = None

        description_block = soup.find("div", class_="describe")
        app_data["description"] = description_block.find(
            "div", attrs={"class": "content", "itemprop": "description"}).text

        screenshots_block = description_block.find("li", class_="amagnificpopup")
        app_data["screenshots"] = [img["src"] for img in screenshots_block.findAll("img")]

        tag_block = soup.find("div", class_="tag")
        app_data["tags"] = [a.text for a in tag_block.find("ul", class_="tag_list").findAll("a")]

        version_link = None
        try:
            version_link = main_dl.find("div", id="down_btns").find("a", class_="go-to-download")["href"]
        except TypeError:
            version_link = main_dl.find("div", id="down_btns").find("a", class_=" go-to-download")["href"]
        finally:
            if version_link is None:
                app_data["download"] = None
                app_data["playstore_only"] = True
            else:
                app_data["download"] = partial(
                    self.__download,
                    version_link)
                app_data["playstore_only"] = False

            return app_data

    def __download(self, version_url, output_dir=os.getcwd(), output_filename=None, progress_bar=True):
        response = self.__scraper.get(version_url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="lxml")
            direct_link = soup.find("a", id="download_link")["href"]

            dl_response = self.__scraper.get(direct_link, stream=True)
            output_filename = (
                Helpers.filename_from_headers(dl_response.headers)
                if output_filename is None else output_filename)
            output_path = os.path.join(output_dir, output_filename)

            filesize = int(dl_response.headers.get('content-length', 0))

            print(f"Starting download of: {output_filename}")
            if progress_bar:
                with open(output_path, 'wb') as file, tqdm(
                    desc=output_path,
                    total=filesize,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as pbar:
                    for data in dl_response.iter_content(chunk_size=1024):
                        size = file.write(data)
                        pbar.update(size)
            else:
                dl_response.raw.read = partial(dl_response.raw.read, decode_content=True)
                with open(output_path, "wb") as file:
                    shutil.copyfileobj(dl_response.raw, file, length=16 * 1024 * 1024)
            print(f"App downloaded to: {output_path}")

            return output_path
        raise Exception(f"Failed to fetch HTML content. {response.status_code} {response.reason}")
