def get_key_name(val):
    keynames = {
        "角色名": "role_name",
        "初始星级": "rarity",
        "职业": "profession",
        "类型": "type",
        "身高": "height",
        "体重": "weight",
        "年龄": "age",
        "生日": "birthday",
        "血型": "blood_type",
        "种族": "race",
        "工会": "union",
        "兴趣": "interest",
        "碎片获取": "fragment_get",
        "外号": "nickname",
        "CV": "cv"
    }

    if val in keynames:
        return keynames[val]
    else:
        return val
