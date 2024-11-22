const controls = {
    'DAG Tree Orientation': 'td',
    'Arrow Length': 10,
    'Node Size': 2,
    '# of Particles': 5,
    'Particle Size': 2,
    'Particle Speed': 0.01,
    'Base Link Length': 1,
    'Server Link Length': 5,
    'Category Link Length': 4,
    'Channel Link Length': 3,
    'Chat Link Length': 2,
    'Message Link Length': 1,
    '[Zoom to fit]': () => graph.zoomToFit(400)
};

const graph = ForceGraph3D()(document.getElementById('3d-graph'));

const gui = new dat.GUI({width: 400});
gui.add(controls, 'DAG Tree Orientation', ['td', 'bu', 'lr', 'rl', 'zout', 'zin', 'radialout', 'radialin', null])
    .onChange(orientation => graph && graph.dagMode(orientation) && graph.numDimensions(3));
gui.add(controls, 'Node Size', 1, 4).onChange(size => graph && graph.nodeResolution(size));
gui.add(controls, 'Arrow Length', 0, 100).onChange(length => graph && graph.linkDirectionalArrowLength(length));
gui.add(controls, '[Zoom to fit]');

const linkLengthsFolder = gui.addFolder('Link Lengths');
linkLengthsFolder.add(controls, 'Base Link Length', 0, 100).onChange(updateLinkDistance);
linkLengthsFolder.add(controls, 'Server Link Length', 0, 10).onChange(updateLinkDistance);
linkLengthsFolder.add(controls, 'Category Link Length', 0, 10).onChange(updateLinkDistance);
linkLengthsFolder.add(controls, 'Channel Link Length', 0, 10).onChange(updateLinkDistance);
linkLengthsFolder.add(controls, 'Chat Link Length', 0, 10).onChange(updateLinkDistance);
linkLengthsFolder.add(controls, 'Message Link Length', 0, 10).onChange(updateLinkDistance);

const particleSettingsFolder = gui.addFolder('Particle Settings');
particleSettingsFolder.add(controls, '# of Particles', 0, 20).onChange(particles => graph && graph.linkDirectionalParticles(particles));
particleSettingsFolder.add(controls, 'Particle Size', 0, 20).onChange(size => graph && graph.linkDirectionalParticleWidth(size));
particleSettingsFolder.add(controls, 'Particle Speed', 0.001, 0.1).onChange(speed => graph && graph.linkDirectionalParticleSpeed(speed));

graph.jsonUrl('./graph_data.json')
    .showNavInfo(true)
    .dagMode(controls['DAG Tree Orientation'])
    .nodeLabel('name')
    .nodeAutoColorBy('type')
    .nodeLabel(node => node.name)
    .nodeRelativeSize(node => node.relative_size ** controls['Node Size'])
    .linkDirectionalArrowLength(controls['Arrow Length'])
    .linkDirectionalArrowRelPos(controls['Show Arrows'] ? 0.5 : 0)
    .linkDirectionalParticles(controls['# of Particles'])
    .linkDirectionalParticleSpeed(controls['Particle Speed'])
    .linkDirectionalParticleWidth(controls['Particle Size'])
    .linkResolution(4);

const linkForce = graph.d3Force('link').distance(link => calculateLinkDistance(link));

function calculateLinkDistance(link) {
    const sourceNode = graph.graphData().nodes.find(node => node.id === link.source);
    const sourceLevel = sourceNode ? sourceNode.level : 1;
    let typeMultiplier = 1;
    if (link.type === 'server') typeMultiplier = controls['Server Link Length'];
    if (link.type === 'category') typeMultiplier = controls['Category Link Length'];
    if (link.type === 'channel') typeMultiplier = controls['Channel Link Length'];
    if (link.type === 'chat') typeMultiplier = controls['Chat Link Length'];
    if (link.type === 'message') typeMultiplier = controls['Message Link Length'];
    return controls['Base Link Length'] * sourceLevel * typeMultiplier;
}

function updateLinkDistance() {
    linkForce.distance(link => calculateLinkDistance(link));
    graph.numDimensions(3);
}