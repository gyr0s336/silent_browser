SPEED_DIAL_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', sans-serif; background: __BG__; min-height: 100vh; color: __TEXT__; padding: 40px 20px; }
.container { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 42px; font-weight: 300; margin-bottom: 40px; text-align: center; letter-spacing: 2px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 20px; margin-bottom: 30px; }
.tile { aspect-ratio: 1; background: __TILE_BG__; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: all 0.2s; position: relative; border: 1px solid __BORDER__; text-decoration: none; color: inherit; }
.tile:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.2); border-color: __ACCENT__; }
.tile .icon { width: 48px; height: 48px; border-radius: 10px; background: __ACCENT__; color: __ICON_TEXT__; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; margin-bottom: 10px; }
.tile .title { font-size: 13px; font-weight: 500; text-align: center; padding: 0 8px; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.footer { text-align: center; margin-top: 40px; color: __MUTED__; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
    <h1>SILENT</h1>
    <div class="grid" id="grid"></div>
    <div class="footer">Управление плитками: ☰ → "Управление Speed Dial"</div>
</div>
<script>
const tiles = __TILES__;
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function render() {
    const grid = document.getElementById('grid');
    grid.innerHTML = '';
    tiles.forEach(t => {
        const a = document.createElement('a');
        a.className = 'tile';
        a.href = '#';
        a.onclick = (e) => { e.preventDefault(); window.location.href = t.url; };
        const letter = (t.title || '?')[0].toUpperCase();
        a.innerHTML = `<div class="icon">${letter}</div><div class="title">${escapeHtml(t.title)}</div>`;
        grid.appendChild(a);
    });
}
render();
</script>
</body>
</html>
"""

def generate_speed_dial_html(bg="#1a1a1a", text="#ffffff", accent="#4a9eff",
                             tile_bg="#2a2a2a", border="#3a3a3a", icon_text="#ffffff",
                             muted="#5f6368", tiles=None):
    import json
    if tiles is None:
        tiles = []
    html = SPEED_DIAL_HTML
    html = html.replace('__BG__', bg).replace('__TEXT__', text)
    html = html.replace('__ACCENT__', accent).replace('__TILE_BG__', tile_bg)
    html = html.replace('__BORDER__', border).replace('__ICON_TEXT__', icon_text)
    html = html.replace('__MUTED__', muted)
    html = html.replace('__TILES__', json.dumps(tiles, ensure_ascii=False))
    return html