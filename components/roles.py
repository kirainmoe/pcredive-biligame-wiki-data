import requests
import urllib.request
import json
import os

from bs4 import BeautifulSoup
from config import app_config
from utils.log import logger
from utils.formatter import get_key_name


# 获取角色列表，返回带有角色名和稀有度的 list
def get_roles_list():
    url = "https://wiki.biligame.com/pcr/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    rarity_div = soup.select(".resp-tab-content")
    result = []

    for index, div in enumerate(rarity_div):
        roles = div.select(".box-js")
        rarity = 3 - index
        for role in roles:
            role_name = role.select("a")[0]["title"]
            result.append({
                "name": role_name,
                "rarity": rarity
            })
    return result


# 爬取角色图鉴
def get_roles_illustration(verbose=True):
    logger("Info", "Start download roles illustrations...", verbose)

    url = "https://wiki.biligame.com/pcr/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    roles_data = soup.select(".box-js")
    result = {}

    # 创建文件夹
    save_path = os.path.join(app_config["data_path"], "illustrations")
    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            logger("Error", "Create download path %s failed!" % save_path, verbose)

    # 下载插图
    for index, role in enumerate(roles_data):
        logger("Info", "Downloading illustrations %d/%d" % (index + 1, len(roles_data)), verbose)
        role_name = role.select("a")[0]["title"]
        role_illustration_url = role.select("img")[0]["src"]
        illustration_save_path = os.path.join(save_path, "%s.jpg" % role_name)
        urllib.request.urlretrieve(role_illustration_url, illustration_save_path)
        result["role_name"] = {
            "role_name": role_name,
            "illustration_url": role_illustration_url,
            "illustration_save_path": illustration_save_path
        }

    logger("OK", "Roles' illustrations has been downloaded to %s!" % save_path, verbose)
    return result


# 爬取角色头像
def get_roles_avatar(role_list=None, verbose=True):
    if not role_list:
        role_list = get_roles_list()
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
    for index, role in enumerate(role_list):
        logger("Info", "Downloading avatars %d/%d" % (index + 1, len(role_list)), verbose)

        role_page_url = base_url + role["name"]
        response = requests.get(role_page_url)
        soup = BeautifulSoup(response.text, "lxml")
        images_url = soup.select('.img-kk')[0]["src"]
        result[role["name"]] = images_url

        avatar_save_path = os.path.join(save_path, "%s.jpg" % role["name"])
        urllib.request.urlretrieve(images_url, avatar_save_path)

    logger("OK", "Roles' avatar has been downloaded to %s!" % save_path, verbose)
    return result


# 爬取角色详情，若爬取失败或角色信息不存在返回空 dict
def get_single_role_detail(role_name=None):
    if role_name is None:
        return {}
    url = "https://wiki.biligame.com/pcr/%s" % role_name
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
def get_all_role_detail(role_list=None):
    if role_list is None:
        role_list = get_roles_list()
    roles_detail = {}
    save_path = os.path.join(app_config["data_path"], "result.json")

    for role in role_list:
        roles_detail[role["name"]] = get_single_role_detail(role["name"])

    with open(save_path, "w") as file:
        file.write(json.dumps(roles_detail, indent=4, ensure_ascii=False))

    return roles_detail
