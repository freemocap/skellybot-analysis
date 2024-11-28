import SpriteText from 'three-spritetext';


const GUIFields = {
    GRAPH_DATA: 'Graph Data',
    CONTROL_TYPE: 'Control Type',
    AUTO_COLOR_BY: 'Auto Color By',
    DAG_TREE_ORIENTATION: 'DAG Tree Orientation',
    NODE_SIZE: 'Node Size',
    BASE_LINK_LENGTH: 'Base Link Length',
    SERVER_LINK_LENGTH: 'Server Link Length',
    CATEGORY_LINK_LENGTH: 'Category Link Length',
    CHANNEL_LINK_LENGTH: 'Channel Link Length',
    CHAT_LINK_LENGTH: 'Chat Link Length',
    MESSAGE_LINK_LENGTH: 'Message Link Length',
    ZOOM_TO_FIT: '[Zoom to fit]'
};


function calculateLinkDistance(link, controls) {
    switch (link.type) {
        case 'parent':
            switch (link.source.type) {
                case 'server':
                    return controls[GUIFields.SERVER_LINK_LENGTH];
                case 'category':
                    return controls[GUIFields.CATEGORY_LINK_LENGTH];
                case 'channel':
                    return controls[GUIFields.CHANNEL_LINK_LENGTH];
                case 'thread':
                    return controls[GUIFields.MESSAGE_LINK_LENGTH];
                default:
                    return controls[GUIFields.MESSAGE_LINK_LENGTH];
            }
        case 'reply':
            return controls[GUIFields.MESSAGE_LINK_LENGTH];
        default:
            return controls[GUIFields.BASE_LINK_LENGTH];
    }
}

function getPrunedTree(graphData, rootId) {
    // Initialize nodes with collapsed and childLinks fields

    const nodesById = Object.fromEntries(graphData.nodes.map(node => [node.id, node]));
    graphData.links.forEach(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        if (!nodesById[sourceId]) {
            console.error("Source node not found for link:", link.source);
            return;
        }
        if (!nodesById[targetId]) {
            console.error("Target node not found for link:", link.target);
            return;
        }

        console.log("Adding child link to source node: ", nodesById[sourceId]);
        nodesById[sourceId].childLinks.push(link);
    });

    const visibleNodes = [];
    const visibleLinks = [];

    (function traverseTree(node = nodesById[rootId]) {
        visibleNodes.push(node);
        if (node.collapsed) return;
        visibleLinks.push(...node.childLinks);
        node.childLinks
            .map(link => ((typeof link.target) === 'object') ? link.target : nodesById[link.target])
            .forEach(traverseTree);
    })();

    return {nodes: visibleNodes, links: visibleLinks};
}

class GraphControls {

    constructor(graph) {
        this.graph = graph;
        this.controls = this.initializeControls();
        this.initGUI();
    }

    initializeControls() {
        return {
            [GUIFields.GRAPH_DATA]: 'graph_data_short_threads.json',
            [GUIFields.CONTROL_TYPE]: 'fly',
            [GUIFields.AUTO_COLOR_BY]: 'type',
            [GUIFields.DAG_TREE_ORIENTATION]: 'radialout',
            [GUIFields.NODE_SIZE]: 2,
            [GUIFields.BASE_LINK_LENGTH]: 1,
            [GUIFields.SERVER_LINK_LENGTH]: 5,
            [GUIFields.CATEGORY_LINK_LENGTH]: 4,
            [GUIFields.CHANNEL_LINK_LENGTH]: 3,
            [GUIFields.CHAT_LINK_LENGTH]: 2,
            [GUIFields.MESSAGE_LINK_LENGTH]: 1,
            [GUIFields.ZOOM_TO_FIT]: () => this.graph.zoomToFit(400)
        };
    }

    initGUI() {
        const gui = new dat.GUI({width: 400});
        this.addGraphDataControl(gui);
        // this.addControlTypeControl(gui);
        this.addDAGTreeOrientationControl(gui);
        this.addNodeSizeControl(gui);
        this.addZoomToFitControl(gui);
        this.addNodeSettingsFolder(gui);
        this.addLinkSettingsFolder(gui);
    }

    addGraphDataControl(gui) {
        gui.add(this.controls, GUIFields.GRAPH_DATA, ['graph_data_chat_clusters.json', 'graph_data_full.json', 'graph_data_short_threads.json', 'test_graph_data.json'])
            .onChange(url => this.graph && this.graph.jsonUrl(url));
    }

    addControlTypeControl(gui) {
        gui.add(this.controls, GUIFields.CONTROL_TYPE, ['fly', 'trackball', 'orbit'])
            .onChange(controlType => {
                console.log(`Setting control type to ${controlType}`);
                if (this.graph) {
                    this.graph.controls().enabled = false; // Disable current controls
                    this.graph.controls({type: controlType}); // Set new control type
                    this.graph.controls().enabled = true; // Enable new controls
                }
            });
    }

    addDAGTreeOrientationControl(gui) {
        gui.add(this.controls, GUIFields.DAG_TREE_ORIENTATION, ['td', 'bu', 'lr', 'rl', 'zout', 'zin', 'radialout', 'radialin', null])
            .onChange(orientation => this.graph && this.graph.dagMode(orientation) && this.graph.numDimensions(3));
    }

    addNodeSizeControl(gui) {
        gui.add(this.controls, GUIFields.NODE_SIZE, 1, 4).onChange(size => this.graph && this.graph.nodeResolution(size));
    }

    addZoomToFitControl(gui) {
        gui.add(this.controls, GUIFields.ZOOM_TO_FIT);
    }

    addNodeSettingsFolder(gui) {
        const nodeSettingsFolder = gui.addFolder('Node Settings');
        nodeSettingsFolder.add(this.controls, GUIFields.NODE_SIZE, 1, 4).onChange(size => this.graph && this.graph.nodeResolution(size));
        nodeSettingsFolder.add(this.controls, GUIFields.AUTO_COLOR_BY, ['group', 'level', 'id'])
            .onChange(colorBy => this.graph && this.graph.nodeAutoColorBy(colorBy));
    }

    addLinkSettingsFolder(gui) {
        const linkSettingsFolder = gui.addFolder('Link Settings');
        linkSettingsFolder.add(this.controls, GUIFields.BASE_LINK_LENGTH, 0, 100).onChange(() => this.updateLinkDistance());
        linkSettingsFolder.add(this.controls, GUIFields.SERVER_LINK_LENGTH, 0, 10).onChange(() => this.updateLinkDistance());
        linkSettingsFolder.add(this.controls, GUIFields.CATEGORY_LINK_LENGTH, 0, 10).onChange(() => this.updateLinkDistance());
        linkSettingsFolder.add(this.controls, GUIFields.CHANNEL_LINK_LENGTH, 0, 10).onChange(() => this.updateLinkDistance());
        linkSettingsFolder.add(this.controls, GUIFields.CHAT_LINK_LENGTH, 0, 10).onChange(() => this.updateLinkDistance());
        linkSettingsFolder.add(this.controls, GUIFields.MESSAGE_LINK_LENGTH, 0, 10).onChange(() => this.updateLinkDistance());
    }


    updateLinkDistance() {
        this.graph.d3Force('link').distance(link => calculateLinkDistance(link, this.controls));
        this.graph.numDimensions(3);
    }
}

class GraphManager {

    constructor() {
        this.graph = ForceGraph3D({controlType: 'orbit'})(document.getElementById('3d-graph'));
        this.controls = new GraphControls(this.graph);
        this.initGraph();
    }

    initGraph() {
        this.graph.jsonUrl(this.controls.controls[GUIFields.GRAPH_DATA])
            .showNavInfo(true)
            .dagMode(this.controls.controls[GUIFields.DAG_TREE_ORIENTATION])
            .nodeLabel('name')
            .nodeAutoColorBy('type')
            .nodeLabel(node => node.name)
            .nodeThreeObject(node => {
                const sprite = new SpriteText(node.name);
                sprite.material.depthWrite = false; // make sprite background transparent
                sprite.color = node.color;
                console.log("Node three object: ", node);
                sprite.textHeight = 8;
                return sprite;
            })
            .onNodeClick(node => {
                    // Aim at node from outside it
                    const distance = 100;
                    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

                    const newPos = node.x || node.y || node.z
                        ? {x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio}
                        : {x: 0, y: 0, z: distance}; // special case if node is in (0,0,0)

                    this.graph.cameraPosition(
                        newPos, // new position
                        node, // lookAt ({ x, y, z })
                        1000  // ms transition duration
                    );
                }
            )
            .onNodeRightClick(node => {
                    node.collapsed = !node.collapsed;
                    this.graph.graphData(getPrunedTree(this.graph.graphData(), node.id));
                }
            )
        ;
        this.graph.d3Force('link').distance(link => calculateLinkDistance(link, this.controls.controls));
    }
}


document.addEventListener('DOMContentLoaded', () => {
    new GraphManager();
});
