"""Illustrated view of the library room, drawn as inline SVG.

render_room_svg(view) draws the room from a small "view" dict of flags:

    {
      "crimson_found": bool,      # crimson volumes discovered on the bookshelf
      "drawer_open": bool,        # desk drawer unlocked
      "drawer_items": [ids],      # items still lying in the open drawer
      "painting_open": bool,      # portrait swung open, alcove visible
      "plate_read": bool,         # brass plate read with the magnifying glass
      "keypad_active": bool,      # all three trials solved
      "door_open": bool,          # player escaped
      "highlight": str | None,    # "bookshelf", "desk", "painting" or "door"
    }

Version 2 builds this dict from the real game state (game_state.scene_view), so the
picture always matches the rules. Version 1 has no game state, so it shows STATIC_VIEW.
The drawing is plain SVG shapes: no image files and no extra libraries.
"""

from __future__ import annotations

STATIC_VIEW = {
    "crimson_found": False, "drawer_open": False, "drawer_items": [], "painting_open": False,
    "plate_read": False, "keypad_active": False, "door_open": False, "highlight": None,
}

GOLD, GOLD_LIGHT, CRIMSON = "#c9a24a", "#f1d58f", "#8b1e2b"
BOOK_COLOURS = ["#5a3d26", "#4a3322", "#6b4a2e", "#3f2b1c", "#7a5634", "#54402c"]
BOOK_WIDTHS = [9, 12, 8, 11, 10, 7, 13, 9, 10, 8, 12, 11]
BOOK_HEIGHTS = [40, 46, 38, 44, 42, 36, 45, 41, 39, 44, 43, 37]


def _defs() -> str:
    return f"""
<defs>
  <linearGradient id="er-wall" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1a130d"/><stop offset="1" stop-color="#2a1f16"/>
  </linearGradient>
  <linearGradient id="er-floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a1d12"/><stop offset="1" stop-color="#150f0a"/>
  </linearGradient>
  <linearGradient id="er-gilt" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#e0c27a"/><stop offset="0.5" stop-color="#a8823a"/><stop offset="1" stop-color="#d9b866"/>
  </linearGradient>
  <linearGradient id="er-night" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0d1828"/><stop offset="1" stop-color="#27466b"/>
  </linearGradient>
  <radialGradient id="er-lamp" cx="0.58" cy="0.55" r="0.55">
    <stop offset="0" stop-color="#f3b54a" stop-opacity="0.16"/>
    <stop offset="1" stop-color="#f3b54a" stop-opacity="0"/>
  </radialGradient>
  <filter id="er-glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>"""


def _bookshelf(crimson_found: bool) -> str:
    parts = ['<g id="er-bookshelf">',
             '<rect x="40" y="38" width="232" height="240" fill="#3b2a1c" stroke="#5a4128" stroke-width="3"/>',
             '<rect x="50" y="46" width="212" height="226" fill="#1c140d"/>']
    for row in range(4):
        shelf_y = 95 + row * 57
        x, i = 54, row * 5
        while x < 252:
            width = BOOK_WIDTHS[i % len(BOOK_WIDTHS)]
            height = BOOK_HEIGHTS[(i * 7 + row) % len(BOOK_HEIGHTS)]
            if x + width > 258:
                break
            crimson = row == 1 and 4 <= (i - row * 5) <= 7
            colour = CRIMSON if crimson else BOOK_COLOURS[(i + row) % len(BOOK_COLOURS)]
            extra = ""
            if crimson and crimson_found:
                extra = f' stroke="{GOLD_LIGHT}" stroke-width="1.5" filter="url(#er-glow)"'
            parts.append(f'<rect x="{x}" y="{shelf_y - height}" width="{width}" height="{height}" '
                         f'fill="{colour}"{extra}/>')
            x += width + 1
            i += 1
        parts.append(f'<rect x="46" y="{shelf_y}" width="220" height="7" fill="#4a3322"/>')
    parts.append("</g>")
    return "".join(parts)


def _desk(drawer_open: bool, drawer_items: list[str]) -> str:
    parts = ['<g id="er-desk">',
             # journal and lamp on the desk top
             '<path d="M392 214 L418 206 L444 214 L418 219 Z" fill="#d8c7a0"/>',
             '<line x1="418" y1="206" x2="418" y2="219" stroke="#8f7a55" stroke-width="1"/>',
             '<rect x="552" y="204" width="22" height="10" rx="2" fill="#8a6a35"/>',
             '<ellipse cx="563" cy="188" rx="9" ry="16" fill="#e8c98a" fill-opacity="0.25" stroke="#b08a3e"/>',
             '<ellipse cx="563" cy="190" rx="3.5" ry="7" fill="#ffcf6b" filter="url(#er-glow)"/>',
             # desk top, body and legs
             '<rect x="350" y="214" width="262" height="12" rx="2" fill="#5a3d26"/>',
             '<rect x="364" y="226" width="234" height="46" fill="#3b2a1c"/>',
             '<rect x="368" y="272" width="14" height="32" fill="#3b2a1c"/>',
             '<rect x="580" y="272" width="14" height="32" fill="#3b2a1c"/>']
    if drawer_open:
        parts += ['<rect x="430" y="236" width="102" height="26" fill="#120d09"/>',
                  '<polygon points="428,262 534,262 552,298 410,298" fill="#2d2016" stroke="#6b4c30"/>',
                  '<rect x="410" y="298" width="142" height="12" fill="#4a3322" stroke="#6b4c30"/>',
                  '<polygon points="434,266 528,266 540,294 422,294" fill="#5c1f26"/>']
        if "brass_key" in drawer_items:
            parts.append('<g filter="url(#er-glow)"><circle cx="452" cy="280" r="5" fill="none" '
                         f'stroke="{GOLD}" stroke-width="2.5"/><line x1="457" y1="280" x2="476" y2="280" '
                         f'stroke="{GOLD}" stroke-width="2.5"/><line x1="471" y1="280" x2="471" y2="286" '
                         f'stroke="{GOLD}" stroke-width="2"/></g>')
        if "magnifying_glass" in drawer_items:
            parts.append('<g filter="url(#er-glow)"><circle cx="505" cy="278" r="7" fill="#a9c3cf" '
                         'fill-opacity="0.35" stroke="#d8c7a0" stroke-width="2"/><line x1="510" y1="283" '
                         'x2="520" y2="291" stroke="#8a6a35" stroke-width="3.5"/></g>')
    else:
        parts += ['<rect x="430" y="236" width="102" height="26" fill="#4a3322" stroke="#6b4c30"/>',
                  f'<circle cx="481" cy="249" r="7" fill="{GOLD}" stroke="#6b4c30"/>',
                  '<circle cx="481" cy="249" r="2" fill="#3b2a1c"/>']
    parts.append("</g>")
    return "".join(parts)


def _painting(painting_open: bool, plate_read: bool) -> str:
    if not painting_open:
        return """<g id="er-painting">
  <rect x="650" y="58" width="122" height="152" fill="url(#er-gilt)" stroke="#6b5636"/>
  <rect x="662" y="70" width="98" height="128" fill="#2a2219"/>
  <ellipse cx="711" cy="112" rx="15" ry="18" fill="#a8916d"/>
  <path d="M684 198 Q686 142 711 136 Q736 142 738 198 Z" fill="#3d2f22"/>
  <rect x="738" y="148" width="5" height="22" fill="#e9dfc9"/>
  <ellipse cx="740.5" cy="144" rx="2.5" ry="4.5" fill="#ffcf6b" filter="url(#er-glow)"/>
  <text x="755" y="194" font-size="6" fill="#8f8068" text-anchor="end" font-family="Georgia, serif">E. Thorne 1852</text>
  <circle cx="711" cy="204" r="2" fill="#2a1d12"/><rect x="710.2" y="204" width="1.6" height="3.5" fill="#2a1d12"/>
</g>"""
    plate_fill = GOLD_LIGHT if plate_read else "#9a7a3a"
    plate_filter = ' filter="url(#er-glow)"' if plate_read else ""
    return f"""<g id="er-painting">
  <rect x="660" y="68" width="102" height="132" fill="#0f0b08" stroke="#3b2a1c" stroke-width="3"/>
  <rect x="668" y="76" width="86" height="116" fill="#17110c"/>
  <rect x="691" y="122" width="40" height="24" rx="2" fill="{plate_fill}"{plate_filter}/>
  <line x1="696" y1="130" x2="726" y2="130" stroke="#5a4128" stroke-width="1"/>
  <line x1="696" y1="135" x2="722" y2="135" stroke="#5a4128" stroke-width="1"/>
  <line x1="696" y1="140" x2="724" y2="140" stroke="#5a4128" stroke-width="1"/>
  <polygon points="650,58 690,74 690,196 650,210" fill="url(#er-gilt)" stroke="#6b5636"/>
  <polygon points="656,68 684,79 684,190 656,200" fill="#2a2219"/>
</g>"""


def _door(keypad_active: bool, door_open: bool) -> str:
    keypad_fill = GOLD_LIGHT if keypad_active or door_open else "#6b5636"
    keypad_filter = ' filter="url(#er-glow)"' if keypad_active or door_open else ""
    keypad = (f'<rect x="790" y="150" width="16" height="30" rx="2" fill="#2a1d12" stroke="{GOLD}"/>'
              f'<g fill="{keypad_fill}"{keypad_filter}>'
              '<circle cx="795" cy="158" r="1.6"/><circle cx="801" cy="158" r="1.6"/>'
              '<circle cx="795" cy="165" r="1.6"/><circle cx="801" cy="165" r="1.6"/>'
              '<circle cx="795" cy="172" r="1.6"/><circle cx="801" cy="172" r="1.6"/></g>')
    arch = "M818 272 V96 Q866 44 914 96 V272 Z"
    if door_open:
        return f"""<g id="er-door">
  <path d="{arch}" fill="url(#er-night)" stroke="#5a4a3a" stroke-width="4"/>
  <circle cx="884" cy="100" r="9" fill="#f1e6cc" filter="url(#er-glow)"/>
  <circle cx="840" cy="120" r="1.2" fill="#f1e6cc"/><circle cx="866" cy="88" r="1" fill="#f1e6cc"/>
  <circle cx="898" cy="140" r="1" fill="#f1e6cc"/><circle cx="850" cy="160" r="1.2" fill="#f1e6cc"/>
  <polygon points="914,96 948,84 948,262 914,272" fill="#2c241d" stroke="#5a4a3a"/>
  {keypad}
</g>"""
    bands = "".join(
        f'<rect x="818" y="{y}" width="96" height="9" fill="#4a4038"/>'
        + "".join(f'<circle cx="{x}" cy="{y + 4.5}" r="2" fill="#7a6b5a"/>' for x in (826, 866, 906))
        for y in (118, 186, 244)
    )
    return f"""<g id="er-door">
  <path d="{arch}" fill="#2c241d" stroke="#5a4a3a" stroke-width="4"/>
  <line x1="850" y1="70" x2="850" y2="272" stroke="#221b15" stroke-width="2"/>
  <line x1="882" y1="62" x2="882" y2="272" stroke="#221b15" stroke-width="2"/>
  {bands}
  <circle cx="902" cy="170" r="5" fill="none" stroke="{GOLD}" stroke-width="2"/>
  {keypad}
</g>"""


def _labels(highlight: str | None) -> str:
    labels = [("bookshelf", 156, "Bookshelf"), ("desk", 481, "Desk &amp; drawer"),
              ("painting", 711, "Painting"), ("door", 866, "Exit door")]
    out = []
    for key, x, text in labels:
        colour = GOLD_LIGHT if key == highlight else "#a8987a"
        weight = "700" if key == highlight else "400"
        out.append(f'<text x="{x}" y="332" font-size="17" fill="{colour}" font-weight="{weight}" '
                   f'text-anchor="middle" font-family="Georgia, serif">{text}</text>')
    return "".join(out)


def render_room_svg(view: dict) -> str:
    """Return the full room illustration as an SVG string."""
    view = {**STATIC_VIEW, **view}
    state_attrs = (f'data-drawer="{"open" if view["drawer_open"] else "locked"}" '
                   f'data-painting="{"open" if view["painting_open"] else "closed"}" '
                   f'data-door="{"open" if view["door_open"] else "locked"}"')
    return (
        f'<svg class="er-room" viewBox="0 0 960 345" role="img" {state_attrs} '
        'aria-label="Illustration of the library room" xmlns="http://www.w3.org/2000/svg" '
        'style="width:100%;height:auto;display:block;border:1px solid #4a3a25;border-radius:8px">'
        f"{_defs()}"
        '<rect width="960" height="345" fill="url(#er-wall)"/>'
        '<rect y="272" width="960" height="73" fill="url(#er-floor)"/>'
        + "".join(f'<line x1="0" y1="{y}" x2="960" y2="{y}" stroke="#241910" stroke-width="1"/>'
                  for y in (290, 312))
        + _bookshelf(view["crimson_found"])
        + _desk(view["drawer_open"], view["drawer_items"])
        + _painting(view["painting_open"], view["plate_read"])
        + _door(view["keypad_active"], view["door_open"])
        + '<rect width="960" height="345" fill="url(#er-lamp)" pointer-events="none"/>'
        + _labels(view["highlight"])
        + "</svg>"
    )
