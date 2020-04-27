from components.roles import get_roles_list, get_roles_avatar, \
    get_roles_illustration, get_all_role_detail, get_single_role_detail

from components.map import get_map_reward

# 获取角色列表
roles_list = get_roles_list()
print(roles_list)

# 获取角色头像，保存到 data_path/avatars 中
get_roles_avatar(roles_list, verbose=True)

# 获取角色插图，保存到 data_path/illustrations 中
get_roles_illustration(verbose=False)

# 获取单个角色的信息
shizuru = get_single_role_detail("星野静流")
print(shizuru)

# 获取所有角色的信息
all_roles = get_all_role_detail(roles_list)

# 获取底图掉落数据
reward = get_map_reward()
print(reward)
