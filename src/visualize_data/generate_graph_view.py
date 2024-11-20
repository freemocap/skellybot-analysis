import json
from pathlib import Path

from src.models.server_data_model import GraphData
from src.utilities.get_most_recent_server_data import get_server_data


def create_graph_view_html(graph_data: GraphData, output_file: str):
    html_template = """

    """

    # Embed the graph data in the HTML template
    graph_data_dict = graph_data.to_simple_dict()
    html_content = html_template.format(graph_data=graph_data_dict)

    # Write the HTML content to a file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)


if __name__ == "__main__":
    # Generate graph data
    server_data, server_data_file_path = get_server_data()
    graph_data = server_data.get_graph_data()
    json_output_path = Path(__file__).parent / 'graph_data_chains_short.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(graph_data.to_simple_dict(), indent=2))
    # Create the HTML file
    html_output_file = str(Path(__file__).parent / 'graph_view.html')
    create_graph_view_html(graph_data=graph_data, output_file=html_output_file)
