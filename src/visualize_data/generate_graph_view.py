import json
from pathlib import Path
from token import STRING

from src.models.server_data_model import GraphData
from src.utilities.get_most_recent_server_data import get_server_data


def create_graph_view_html(graph_data: GraphData, output_file: str):
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>3D Force-Directed Graph</title>
      <style>
        body {{ margin: 0; }}
        #3d-graph {{ width: 100vw; height: 100vh; }}
      </style>
      <script src="//unpkg.com/3d-force-graph"></script>
    </head>
    <body>
      <div id="3d-graph"></div>
      <script>
        const graphData = {graph_data};
      
        const Graph = ForceGraph3D()
          (document.getElementById('3d-graph'))
            .graphData(graphData)
            .nodeLabel(node => node.name)
            .linkDirectionalArrowLength(3)
            .linkDirectionalArrowRelPos(1)
            .linkDirectionalParticles(4)
            .linkDirectionalParticleSpeed(0.01);
      </script>
      
    </body>
    </html>
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
    json_output_path = Path(__file__).parent / 'graph_data.json'
    with open(json_output_path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(graph_data.to_simple_dict(), indent=2))
    # Create the HTML file
    html_output_file = str(Path(__file__).parent / 'graph_view.html')
    create_graph_view_html(graph_data=graph_data, output_file=html_output_file)
