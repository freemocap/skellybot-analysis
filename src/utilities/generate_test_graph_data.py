import json

def itergoup(group_count):
    group_count += 1
    return group_count

def generate_test_json():
    nodes = []
    links = []
    data = {"nodes": nodes, "links": links}
    srvr_num = "srvr-1"
    cat_count = 2
    chnl_count = 2
    thd_count = 2
    msg_count = 2
    group_count = 0

    # Add server node
    nodes.append({
        "id": srvr_num,
        "type": "server",
        "group": itergoup(group_count),
        "level": 0
    })

    for cat_num in range(1, cat_count + 1):
        cat_name = f"cat-{cat_num}"
        nodes.append({
            "id": cat_name,
            "type": "category",
            "group": itergoup(group_count),
            "level": 1
        })
        links.append({
            "source": srvr_num,
            "target": cat_name,
            "directional": True,
            "type": "parent",
            "group": itergoup(group_count),
            "relative_length": 1.0
        })

        for chnl_num in range(1, chnl_count + 1):
            chnl_name = f"chnl-{cat_num}-{chnl_num}"
            nodes.append({
                "id": chnl_name,
                "type": "channel",
                "group": itergoup(group_count),
                "level": 2
            })
            links.append({
                "source": cat_name,
                "target": chnl_name,
                "directional": True,
                "type": "parent",
                "group": itergoup(group_count),
                "relative_length": 1.0
            })
            for thd_num in range(1, thd_count + 1):
                thd_name = f"thd-{cat_num}-{chnl_num}-{thd_num}"
                nodes.append({
                    "id": thd_name,
                    "type": "thread",
                    "group": itergoup(group_count),
                    "level": 3
                })
                links.append({
                    "source": chnl_name,
                    "target": thd_name,
                    "directional": True,
                    "type": "parent",
                    "group": itergoup(group_count),
                    "relative_length": 1.0
                })
                previous_msg_name = thd_name
                for msg_num in range(1, msg_count + 1):
                    msg_name = f"msg-{cat_num}-{chnl_num}-{thd_num}-{msg_num}"
                    nodes.append({
                        "type": "message",
                        "id": msg_name,
                        "group": itergoup(group_count),
                        "level": 4
                    })

                    # links.append({
                    #     "source": thd_name,
                    #     "target": msg_name,
                    #     "directional": True,
                    #     "type": "parent",
                    #     "group": itergoup(group_count),
                    #     "relative_length": 1.0
                    # })
                    if previous_msg_name:

                        links.append({
                            "source": previous_msg_name,
                            "target": msg_name,
                            "directional": True,
                            "type": "reply",
                            "group": itergoup(group_count),
                            "relative_length": 1.0
                        })
                    previous_msg_name = msg_name

    return json.dumps(data, indent=2)

# Generate the JSON and print it
test_json = generate_test_json()
with open("../../docs/test_graph_data.json", "w", encoding='utf-8') as f:
    f.write(test_json)
print(test_json)