import requests
import urllib.request
import json
import os

from bs4 import BeautifulSoup
from config import app_config
from utils.log import logger


# 获取装备列表
def get_equipment_list(write_to_file="equipment_list.json"):
    url = "https://wiki.biligame.com/pcr/%E8%A3%85%E5%A4%87%E4%B8%80%E8%A7%88"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.select('#wiki_table')[0]
    equipments = table.select('span')

    result = []
    for index, equip in enumerate(equipments):
        name = equip.select('a')[0]["title"]
        result.append({
            "id": index,
            "equipment_name": name,
        })

    if write_to_file:
        save_path = os.path.join(app_config["data_path"], write_to_file)
        with open(save_path, "w+") as file:
            file.write(json.dumps(result, indent=4, ensure_ascii=False))

    return result


# 下载装备图鉴
def get_equipment_image(verbose=False):
    url = "https://wiki.biligame.com/pcr/%E8%A3%85%E5%A4%87%E4%B8%80%E8%A7%88"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.select('#wiki_table')[0]
    equipments = table.select('span')

    result = {}
    save_path = os.path.join(app_config["data_path"], "equipments")
    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            logger("Error", "Create download path %s failed!" % save_path, verbose)

    for index, equip in enumerate(equipments):
        logger("Info", "Downloading equipment image %d/%d" % (index, len(equipments)), verbose)

        name = equip.select('a')[0]["title"]
        image_url = equip.select('img')[0]["src"]
        equip_save_path = os.path.join(save_path, "%d.png" % index)
        urllib.request.urlretrieve(image_url, equip_save_path)
        result[name] = {
            "id": index,
            "equipment_name": name,
            "equipment_image_url": image_url,
            "equipment_image_path": "%d.png" % index
        }

    with open(os.path.join(save_path, "equipments.json"), "w+") as file:
        file.write(json.dumps(result, indent=4, ensure_ascii=False))

    return result


# 获取装备详情
def get_equipment_detail(name):
    base_url = "https://wiki.biligame.com/pcr/"
    wiki_page_url = base_url + name
    response = requests.get(wiki_page_url)
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.select('.wikitable')[0]

    if len(table) == 0:
        return {}
    tr_units = table.select('tr')
    result = {
        "name": name,
        "description": tr_units[1].select('td b')[0].text,
        "functions": {}
    }
    for i in range(2, len(tr_units)):
        try:
            func_name = tr_units[i].select('th b')[0].text
            func_val = tr_units[i].select('td center')[0].text

            if func_val.strip() != "":
                result["functions"][func_name.strip()] = func_val.strip()
        except IndexError:
            pass
    return result
