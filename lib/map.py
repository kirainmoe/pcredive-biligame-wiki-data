import requests
import json
import os

from bs4 import BeautifulSoup
from config import app_config


# 获取地图掉落信息
def get_map_reward():
    url = "https://wiki.biligame.com/pcr/地图掉落#.E6.99.AE.E9.80.9A.E9.9A.BE.E5.BA.A6"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    map_reward_tables = soup.select(".wikitable")
    result = {}
    for mp in map_reward_tables:
        tr_units = mp.select('tr')
        for i in range(1, len(tr_units)):
            map_name = tr_units[i].select('th a')[0]["title"].strip()        # 地图名称
            primary_reward_tag = tr_units[i].select('td')[0].select('a')
            second_reward_tag = tr_units[i].select('td')[1].select('a')
            primary_reward = []
            second_reward = []
            for item in primary_reward_tag:
                primary_reward.append(item["title"].strip())
            for item in second_reward_tag:
                second_reward.append(item["title"].strip())
            result[map_name] = {
                "primary_reward": primary_reward,
                "second_reward": second_reward
            }

    save_path = os.path.join(app_config["data_path"], "reward.json")
    with open(save_path, "w") as file:
        file.write(json.dumps(result, indent=4, ensure_ascii=False))
    return result
