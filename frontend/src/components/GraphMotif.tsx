// Ilustración de la cabecera: una página de PDF que se convierte en un grafo de conocimiento.
const NODES = [
  { x: 110, y: 60, r: 5 },
  { x: 165, y: 35, r: 7, kind: 'secondary' },
  { x: 225, y: 62, r: 5 },
  { x: 280, y: 38, r: 4 },
  { x: 130, y: 125, r: 5 },
  { x: 190, y: 105, r: 9, kind: 'primary' },
  { x: 255, y: 128, r: 5 },
  { x: 200, y: 160, r: 4 },
]

const EDGES = [
  [0, 1], [1, 2], [2, 3], [0, 4], [1, 5], [4, 5],
  [5, 2], [5, 6], [2, 6], [4, 7], [5, 7], [6, 7],
]

export function GraphMotif() {
  return (
    <svg className="graph-motif" viewBox="0 0 300 180" aria-hidden="true">
      <g className="page">
        <path d="M8 40h42l14 14v60H8z" />
        <path className="fold" d="M50 40v14h14" />
        {[62, 72, 82, 92, 102].map((y, i) => (
          <line key={y} x1="16" x2={i % 2 ? 46 : 56} y1={y} y2={y} />
        ))}
      </g>
      <path className="flow" d="M66 77 C 85 77, 90 62, 104 61" />
      {EDGES.map(([a, b]) => (
        <line key={`${a}-${b}`} className="edge" x1={NODES[a].x} y1={NODES[a].y} x2={NODES[b].x} y2={NODES[b].y} />
      ))}
      {NODES.map((node, i) => (
        <circle
          key={i}
          className={`node ${node.kind ?? ''}`}
          cx={node.x}
          cy={node.y}
          r={node.r}
          style={{ animationDelay: `${i * 0.35}s` }}
        />
      ))}
    </svg>
  )
}
