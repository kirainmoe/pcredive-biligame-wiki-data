import requests
import urllib.request
import json
import os

from bs4 import BeautifulSoup
from config import app_config
from utils.log import logger
from utils.formatter import get_key_name


# 获取角色列表，返回带有角色名和稀有度的 list
def get_characters_list():
    url = "https://wiki.biligame.com/pcr/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    rarity_div = soup.select(".resp-tab-content")
    result = []

    for index, div in enumerate(rarity_div):
        characters = div.select(".box-js")
        rarity = 3 - index
        for character in characters:
            character_name = character.select("a")[0]["title"]
            result.append({
                "name": character_name,
                "rarity": rarity
            })
    return result


# 爬取角色图鉴
def get_characters_illustration(verbose=True):
    logger("Info", "Start download characters illustrations...", verbose)

    url = "https://wiki.biligame.com/pcr/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    characters_data = soup.select(".box-js")
    result = {}

    # 创建文件夹
    save_path = os.path.join(app_config["data_path"], "illustrations")
    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            logger("Error", "Create download path %s failed!" % save_path, verbose)

    # 下载插图
    for index, character in enumerate(characters_data):
        logger("Info", "Downloading illustrations %d/%d" % (index + 1, len(characters_data)), verbose)
        character_name = character.select("a")[0]["title"]
        character_illustration_url = character.select("img")[0]["src"]
        illustration_save_path = os.path.join(save_path, "%s.jpg" % character_name)
        urllib.request.urlretrieve(character_illustration_url, illustration_save_path)
        result["character_name"] = {
            "character_name": character_name,
            "illustration_url": character_illustration_url,
            "illustration_save_path": illustration_save_path
        }

    logger("OK", "Character' illustrations has been downloaded to %s!" % save_path, verbose)
    return result


# 爬取角色头像
def get_characters_avatar(character_list=None, verbose=True):
    if not character_list:
        character_list = get_characters_list()
    base_url = "https://wiki.biligame.com/pcr/"
    result = {}

    # 创建文件夹
    save_path = os.path.join(app_config["data_path"], "avatars")
    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            logger("Error", "Create download path %s failed!" % save_path, verbose)

    # 下载头像
    for index, character in enumerate(character_list):
        logger("Info", "Downloading avatars %d/%d" % (index + 1, len(character_list)), verbose)

        character_page_url = base_url + character["name"]
        response = requests.get(character_page_url)
        soup = BeautifulSoup(response.text, "lxml")
        images_url = soup.select('.img-kk')[0]["src"]
        result[character["name"]] = images_url

        avatar_save_path = os.path.join(save_path, "%s.png" % character["name"])
        urllib.request.urlretrieve(images_url, avatar_save_path)

    logger("OK", "Character' avatar has been downloaded to %s!" % save_path, verbose)
    return result


# 爬取角色详情，若爬取失败或角色信息不存在返回空 dict
def get_single_character_detail(character_name=None):
    if character_name is None:
        return {}
    url = "https://wiki.biligame.com/pcr/%s" % character_name
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    tables = soup.select('#sidebar .wikitable')

    result = {}
    if len(tables) == 0:
        return {}
    try:
        # 角色信息
        units = tables[0].select('tr')
        for unit in units:
            key_text = unit.select('th')[0].text
            key_name = get_key_name(key_text.strip())

            value_text = unit.select('td')[0].text.strip() if key_name != "rarity" \
                else len(unit.select('td img'))
            result[key_name] = value_text
    except Exception:
        pass

    # 获取技能信息
    try:
        cur_node = soup.select("span[id='连结爆发']")[0].parent.next_sibling
        table_count = 0
        while table_count < 4:
            skill_table = None
            if cur_node.name == "table":
                skill_table = cur_node
                table_count += 1
            elif cur_node.name == "div" and len(cur_node.select('table')) > 0:
                skill_table = cur_node.select('table')[0]
                table_count += 1
            cur_node = cur_node.next_sibling

            if skill_table is not None:
                skill_name = skill_table.select('th')
                skill_effect = skill_table.select('td')

                # 连结爆发
                if table_count == 1:
                    result["connect_skill"] = {
                        "skill_name": skill_name[0].text.strip(),
                        "skill_effect": skill_effect[1].text.strip(),
                        "skill_description": skill_effect[2].text.strip()
                    }

                # 普通技能
                if table_count == 2:
                    result["skills"] = []
                    for index, name in enumerate(skill_name):
                        result["skills"].append({
                            "skill_name": name.text.strip(),
                            "skill_effect": skill_effect[index * 2 + 1].text.strip(),
                            "skill_description": skill_effect[index * 2 + 2].text.strip()
                        })

                # EX 技能
                if table_count == 3:
                    result["ex_skill"] = {
                        "skill_name": skill_name[0].text.strip(),
                        "skill_effect": skill_effect[1].text.strip(),
                        "skill_description": skill_effect[2].text.strip()
                    }

                # 角色达到 5 星后
                if table_count == 4:
                    result["ex_plus_skill"] = {
                        "skill_name": skill_name[0].text.strip(),
                        "skill_effect": skill_effect[1].text.strip(),
                        "skill_description": skill_effect[2].text.strip()
                    }
    except Exception:
        pass

    # 获取装备信息
    try:
        cur_node = soup.select("span[id='装备']")[0].parent.next_sibling
        while cur_node.name != "table":
            cur_node = cur_node.next_sibling

        result["equipment"] = {}
        equipment_table = cur_node.select('tr')
        for tr_unit in equipment_table:
            rank = tr_unit.select('th')[0].text.strip()
            equipments = []
            equipment_tag = tr_unit.select('td a')
            for item in equipment_tag:
                equipments.append(item["title"].strip())
            result["equipment"][rank] = equipments
    except Exception:
        pass

    return result


# 获取所有角色的详情
def get_all_character_detail(character_list=None):
    if character_list is None:
        character_list = get_characters_list()
    characters_detail = {}
    save_path = os.path.join(app_config["data_path"], "characters.json")

    for character in character_list:
        characters_detail[character["name"]] = get_single_character_detail(character["name"])

    with open(save_path, "w") as file:
        file.write(json.dumps(characters_detail, indent=4, ensure_ascii=False))

    return characters_detail
