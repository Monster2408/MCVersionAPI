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

        tbody = table.find("tbody")
        trs = tbody.find_all("tr")

        root = ET.Element("root")
        final_protocol = ""

        for tr in trs:
            tds = tr.find_all("td")
            if not tds:
                continue

            version = tds[0].text.strip()
            link = tds[0].find("a")

            data_version = ""
            if link:
                link_url = urljoin(url, link.get("href"))
                
                print(link_url)
                
                link_content = await fetch(session, link_url)
                link_soup = BeautifulSoup(link_content, "html.parser")

                link_table = link_soup.find("table", class_="infobox-rows")
                if link_table:
                    data_version_cell = link_table.find("th", string="Data version")
                    if data_version_cell:
                        data_version = data_version_cell.find_next_sibling("td").text.strip()

            protocol = tds[1].text.strip() if len(tds) > 1 else final_protocol
            final_protocol = protocol

            # XMLノードを作成
            version_child = ET.SubElement(root, "version")
            version_child.set("version", version)

            protocol_child = ET.SubElement(version_child, "protocol")
            protocol_child.text = protocol

            data_version_child = ET.SubElement(version_child, "data_version")
            data_version_child.text = data_version

        # XMLファイルに書き込む
        tree = ET.ElementTree(root)
        ET.indent(tree, space="    ")
        tree.write("mc_version.xml", encoding="utf-8", xml_declaration=True)

async def main():
    await load_mc_version()

if __name__ == "__main__":
    asyncio.run(main())
