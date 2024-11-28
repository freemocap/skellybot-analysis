from typing import Any

from src.utilities.json_datatime_encoder import JSONDateTimeEncoder

if __name__ == "__main__":
    import json
    from pathlib import Path
    from src.utilities.get_most_recent_server_data import get_server_data

    # Generate graph data
    server_data, server_data_file_path = get_server_data()
    graph_data = server_data.get_graph_data()

    json_output_path = Path(__file__).parent.parent.parent/ 'docs' / 'graph_data_chat_clusters.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        # file.write(json.dumps(graph_data.model_dump(),indent=2))
        json.dump(graph_data.model_dump(), file, indent=2, ensure_ascii=False, cls=JSONDateTimeEncoder)