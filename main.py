# -*- coding: UTF-8 -*-
import asyncio
from xml.etree import ElementTree as ET
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin

async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()

async def load_mc_version():
    url = "https://minecraft.fandom.com/wiki/Protocol_version"

    async with ClientSession() as session:
        # ページを取得
        page_content = await fetch(session, url)
        soup = BeautifulSoup(page_content, "html.parser")

        # <table class="wikitable sortable jquery-tablesorter">を取得
        table = soup.find("table", class_="wikitable sortable jquery-tablesorter")
        if not table:
            raise RuntimeError("テーブルが見つかりませんでした。")

        root = ET.Element("root")
        final_protocol = ""
        rowspan_protocol = None  # rowspan対応用

        tbody = table.find("tbody")
        trs = tbody.find_all("tr")

        for tr in trs:
            tds = tr.find_all("td")
            if not tds:
                continue

            version = tds[0].text.strip()
            link = tds[0].find("a")

            # rowspan対応
            if len(tds) > 1:
                protocol = tds[1].text.strip()
                if tds[1].has_attr("rowspan"):
                    rowspan_protocol = protocol
            else:
                protocol = rowspan_protocol  # 前回のrowspan値を再利用

            data_version = ""
            link_url = ""
            if link:
                href = link.get("href")
                link_url = urljoin(url, href)

                link_content = await fetch(session, link_url)
                link_soup = BeautifulSoup(link_content, "html.parser")

                link_table = link_soup.find("table", class_="infobox-rows")
                if link_table:
                    data_version_cell = link_table.find("th", string="Data version")
                    if data_version_cell:
                        data_version = data_version_cell.find_next_sibling("td").text.strip()
                else:
                    # 代替方法
                    link_h3s = link_soup.find_all("h3", class_="pi-data-label pi-secondary-font")
                    for h3 in link_h3s:
                        if h3.text == "Data version":
                            data_version = h3.find_next_sibling("div").text.strip()
                            break

            # XMLノードを作成
            version_child = ET.SubElement(root, "version")
            version_child.set("version", version)

            protocol_child = ET.SubElement(version_child, "protocol")
            protocol_child.text = protocol

            data_version_child = ET.SubElement(version_child, "data_version")
            data_version_child.text = data_version

            link_child = ET.SubElement(version_child, "link")
            link_child.text = link_url

        # XMLファイルに書き
