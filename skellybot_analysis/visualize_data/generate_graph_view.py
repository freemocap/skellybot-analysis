import asyncio

from skellybot_analysis.models.data_models.graph_data_models import GraphData
from skellybot_analysis.utilities.json_datatime_encoder import JSONDateTimeEncoder

if __name__ == "__main__":
    import json
    from pathlib import Path
    from skellybot_analysis.utilities.get_most_recent_server_data import get_server_data

    # Generate graph data
    server_data, server_data_file_path = get_server_data()
    if not isinstance(server_data.graph_data, GraphData):
        asyncio.run(server_data.calculate_graph_data())
    json_output_path = Path(__file__).parent.parent.parent / 'docs' / 'datasets' / 'graph_data.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        # file.write(json.dumps(graph_data.model_dump(),indent=2))
        json.dump(server_data.graph_data.model_dump(), file, indent=2, ensure_ascii=False, cls=JSONDateTimeEncoder)
