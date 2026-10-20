"""Local, deterministic SVG flow diagrams for Blogger-compatible article HTML."""
from __future__ import annotations

from html import escape
from textwrap import wrap


NODE_WIDTH = 164
NODE_HEIGHT = 62
HORIZONTAL_GAP = 76
VERTICAL_GAP = 38
PADDING = 24


def parse_flow_chains(specification: str) -> list[list[str]]:
    """Parse one or more simple, explicitly authored arrow-separated flows."""
    lines = [line.strip() for line in specification.splitlines() if line.strip()]
    if not lines or len(lines) > 4:
        raise ValueError("Add one to four flow lines.")

    chains: list[list[str]] = []
    for line in lines:
        nodes = [node.strip() for node in line.split("->")]
        if len(nodes) < 2 or len(nodes) > 6 or any(not node for node in nodes):
            raise ValueError("Each flow needs two to six labels separated by ->.")
        if any(len(node) > 48 for node in nodes):
            raise ValueError("Keep each diagram label to 48 characters or fewer.")
        chains.append(nodes)
    return chains


def render_flow_diagram(specification: str, caption: str, diagram_id: str) -> str:
    """Build a responsive, self-contained SVG from user-authored process steps."""
    chains = parse_flow_chains(specification)
    max_nodes = max(len(chain) for chain in chains)
    width = PADDING * 2 + max_nodes * NODE_WIDTH + (max_nodes - 1) * HORIZONTAL_GAP
    height = PADDING * 2 + len(chains) * NODE_HEIGHT + (len(chains) - 1) * VERTICAL_GAP
    safe_id = "".join(character for character in diagram_id if character.isalnum()) or "flow"
    title_id = f"diagram-title-{safe_id}"
    description_id = f"diagram-description-{safe_id}"
    safe_caption = escape(caption.strip() or "Process flow", quote=True)

    elements = [
        f'<figure class="article-diagram" role="img" aria-labelledby="{title_id} {description_id}" '
        'style="max-width:100%;overflow-x:auto;">',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="display:block;max-width:none;" '
        f'role="img" aria-labelledby="{title_id} {description_id}" preserveAspectRatio="xMidYMid meet">',
        f'<title id="{title_id}">{safe_caption}</title>',
        f'<desc id="{description_id}">Flow diagram: '
        f'{escape("; then ".join(" then ".join(chain) for chain in chains), quote=True)}</desc>',
        f'<defs><marker id="arrow-{safe_id}" markerWidth="10" markerHeight="10" refX="8" refY="5" '
        'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,5 L0,10 z" fill="#818cf8"/></marker></defs>',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="16" '
        'fill="#0f172a" stroke="#334155"/>',
    ]

    for row, chain in enumerate(chains):
        y = PADDING + row * (NODE_HEIGHT + VERTICAL_GAP)
        for column, label in enumerate(chain):
            x = PADDING + column * (NODE_WIDTH + HORIZONTAL_GAP)
            if column:
                previous_x = x - NODE_WIDTH - HORIZONTAL_GAP
                center_y = y + NODE_HEIGHT / 2
                elements.append(
                    f'<line x1="{previous_x + NODE_WIDTH}" y1="{center_y:g}" '
                    f'x2="{x - 10}" y2="{center_y:g}" stroke="#818cf8" stroke-width="3" '
                    f'marker-end="url(#arrow-{safe_id})"/>'
                )
            elements.append(
                f'<rect x="{x}" y="{y}" width="{NODE_WIDTH}" height="{NODE_HEIGHT}" rx="12" '
                'fill="#1e293b" stroke="#6366f1" stroke-width="2"/>'
            )
            label_lines = wrap(label, width=20, break_long_words=True, break_on_hyphens=True) or [""]
            label_spans = "".join(
                f'<tspan x="{x + NODE_WIDTH / 2:g}" dy="18">{escape(line, quote=True)}</tspan>'
                for line in label_lines[1:]
            )
            label_y = y + NODE_HEIGHT / 2 - (len(label_lines) - 1) * 9
            elements.append(
                f'<text x="{x + NODE_WIDTH / 2:g}" y="{label_y:g}" '
                'fill="#f8fafc" font-family="sans-serif" font-size="15" font-weight="600" '
                f'text-anchor="middle" dominant-baseline="middle">{escape(label_lines[0], quote=True)}'
                f'{label_spans}</text>'
            )

    elements.append("</svg>")
    elements.append(f"<figcaption>{safe_caption}</figcaption></figure>")
    return "".join(elements)
