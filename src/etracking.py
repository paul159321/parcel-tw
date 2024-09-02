import io
import json
import re
import logging

import pytesseract
import requests
from bs4 import BeautifulSoup, Tag
from PIL import Image


class Etracking:
    url = "https://eservice.7-11.com.tw/e-tracking/"
    url_search = url + "search.aspx"

    def __init__(self):
        self.session = requests.Session()

    def search(self, package_id: str):
        if not self._is_valid_package_id(package_id):
            return None

        response = self.session.get(self.url_search)
        soup = BeautifulSoup(response.text, "html.parser")

        view_state = self._get_payload_value(soup, "__VIEWSTATE")
        view_state_generator = self._get_payload_value(soup, "__VIEWSTATEGENERATOR")
        validate_image = self._get_validate_image(response.text)
        code = self._get_code(validate_image)

        payload = {
            "__EVENTTARGET": "submit",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": view_state,
            "__VIEWSTATEGENERATOR": view_state_generator,
            "txtProductNum": package_id,
            "tbChkCode": code,
            "txtIMGName": "",
            "txtPage": 1,
        }

        response = self.session.post(self.url_search, data=payload)

        if response.status_code != 200:
            return None

        return self.parse_response(response.text)

    def _is_valid_package_id(self, package_id: str):
        return len(package_id) == 8 or len(package_id) == 11 or len(package_id) == 12

    def _get_payload_value(self, soup: BeautifulSoup, key: str):
        tag = soup.find("input", id=key)
        if isinstance(tag, Tag):
            return tag.get("value")
        else:
            logging.error(f"Failed to get {key}")

    def _get_validate_image(self, html) -> Image.Image:
        """Get validate image from 7-11 e-tracking website"""
        validate_image_url = ""
        url_suffix = re.search(r'src="(ValidateImage\.aspx\?ts=[0-9]+)"', html)
        if url_suffix is not None:
            validate_image_url = self.url + url_suffix.group(1)

        try:
            response = self.session.get(validate_image_url)
        except requests.exceptions.RequestException:
            raise Exception("Failed to get validate image")

        return Image.open(io.BytesIO(response.content))

    def _get_code(self, image: Image.Image) -> str:
        tesseract_config = "-c tessedit_char_whitelist=0123456789 --psm 8"
        code = pytesseract.image_to_string(image, config=tesseract_config).strip()
        return code

    def parse_response(self, html: str):
        json_data = {
            "msg": "",
            "m_news": "",
            "result": {"info": {}, "shipping": {"timeline": []}},
        }
        soup = BeautifulSoup(html, "html.parser")

        # check if there is any alert message
        script = soup.find_all("script")
        for i in script:
            if "alert(" in i.get_text():
                return {"msg": i.get_text().split("alert('")[1].split("');")[0]}

        # check if there is any error message
        lbmsg = soup.find("span", id="lbMsg")
        if lbmsg is not None and lbmsg.get_text() != "":
            return {"msg": lbmsg.get_text()}

        content_result = soup.find("div", id="content_result")
        if content_result is None:
            return {"msg": "查無資料"}

        # m_news
        json_data["m_news"] = content_result.find("div", {"class": "m_news"}).get_text()
        # json_data["m_news"] = content_result.find("div", class_="m_news").get_text()

        # result
        result = content_result.find("div", class_="result")

        # info
        info = result.find("div", class_="info")
        info_list = info.find_all("span")
        for i in info_list:
            json_data["result"]["info"][i.get("id")] = i.get_text()
        json_data["result"]["info"]["servicetype"] = info.find(
            "h4", id="servicetype"
        ).get_text()

        # shipping
        shipping = result.find("div", class_="shipping")
        shipping_list = shipping.find_all("p")
        for i in shipping_list:
            json_data["result"]["shipping"]["timeline"].append(i.get_text())

        json_data["msg"] = "success"

        return json_data


if __name__ == "__main__":
    res = Etracking().search("87717609641")
    print(json.dumps(res, indent=4, ensure_ascii=False))
    res = Etracking().search("H13804177658")
    print(json.dumps(res, indent=4, ensure_ascii=False))
