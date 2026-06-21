from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
import pandas as pd
import os
import io

app = FastAPI()

CSV_PATH = "/app/output/medieval_poetess.csv"
FIELDS = ["author", "original_text", "date", "source_name", "source_link"]

def load_df():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        for f in FIELDS:
            if f not in df.columns:
                df[f] = ""
        if "validated" not in df.columns:
            df["validated"] = False
    else:
        df = pd.DataFrame(columns=FIELDS + ["validated"])
    return df

def save_df(df):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df.to_csv(CSV_PATH, index=False)

STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#121212;--text:#fff;--muted:#737373;--green:#33FFA2;--violet:#FF33FF;--card:#1A1A1A;--border:#2A2A2A;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Roboto',sans-serif;font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased;}
a{text-decoration:none;color:inherit;transition:color .2s;}
a:hover{color:var(--green);}
header{padding:1.5rem 5%;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(18,18,18,.95);backdrop-filter:blur(10px);z-index:100;display:flex;justify-content:space-between;align-items:center;}
.logo{font-size:1.4rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text);}
.logo span{color:var(--violet);}
nav{display:flex;gap:2rem;font-size:.8rem;font-weight:500;text-transform:uppercase;letter-spacing:1px;}
nav a{color:var(--muted);padding-bottom:4px;}
nav a:hover{color:var(--text);}
nav a.active{color:var(--text);border-bottom:2px solid var(--green);}
.container{max-width:960px;margin:0 auto;padding:2.5rem 5%;}
.page-title{font-size:1.8rem;font-weight:300;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.page-sub{color:var(--muted);font-size:.85rem;margin-bottom:2rem;letter-spacing:.5px;}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 20px;border-radius:2px;font-size:.75rem;font-weight:500;cursor:pointer;border:none;text-transform:uppercase;letter-spacing:1px;transition:all .2s;}
.btn-primary{background:transparent;color:var(--green);border:1px solid var(--green);}
.btn-primary:hover{background:var(--green);color:var(--bg);}
.btn-secondary{background:transparent;color:var(--muted);border:1px solid var(--border);}
.btn-secondary:hover{border-color:var(--muted);color:var(--text);}
.btn-success{background:var(--green);color:var(--bg);border:1px solid var(--green);}
.btn-success:hover{background:transparent;color:var(--green);}
.card{background:var(--card);border:1px solid var(--border);border-radius:2px;padding:24px;margin-bottom:12px;transition:border-color .2s;}
.card:hover{border-color:#444;}
.progress-wrap{background:var(--border);border-radius:99px;height:3px;margin:12px 0 4px;}
.progress-fill{height:100%;background:var(--green);border-radius:99px;transition:width .4s;}
.tag-validated{display:inline-block;color:var(--green);border:1px solid var(--green);border-radius:20px;padding:2px 12px;font-size:.7rem;font-weight:500;letter-spacing:1px;text-transform:uppercase;}
.tag-pending{display:inline-block;color:var(--muted);border:1px solid var(--border);border-radius:20px;padding:2px 12px;font-size:.7rem;font-weight:500;letter-spacing:1px;text-transform:uppercase;}
label{display:block;font-size:.7rem;font-weight:500;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;}
input[type=text],textarea{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:2px;font-family:'Roboto',sans-serif;font-size:14px;background:#111;color:var(--text);transition:border .2s;}
input[type=text]:focus,textarea:focus{outline:none;border-color:var(--green);background:#161616;}
textarea{min-height:140px;resize:vertical;}
.form-group{margin-bottom:20px;}
hr{border:none;border-top:1px solid var(--border);margin:24px 0;}
.flex{display:flex;gap:12px;align-items:center;}
.flex-between{display:flex;justify-content:space-between;align-items:center;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
</style>
"""

def base(content: str, nav_collect="", nav_add="") -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Medieval Poetess — Collecte</title>
{STYLE}
</head>
<body>
<header>
  <a href="/" class="logo"><span>.</span>medieval poetess</a>
  <nav>
    <a href="/" class="{nav_collect}">Collecte</a>
    <a href="/add" class="{nav_add}">+ Ajouter</a>
    <a href="/export">↓ Exporter</a>
  </nav>
</header>
<div class="container">{content}</div>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def index():
    df = load_df()
    total = len(df)
    validated = int(df["validated"].sum()) if total > 0 else 0
    pct = int(validated / total * 100) if total > 0 else 0

    rows = ""
    for i, row in df.iterrows():
        author = str(row.get("author", "") or "(sans nom)")
        date = str(row.get("date", "") or "")
        source = str(row.get("source_name", "") or "Wikipedia")
        is_val = bool(row.get("validated", False))
        tag = '<span class="tag-validated">✓ Validée</span>' if is_val else '<span class="tag-pending">À valider</span>'
        meta = f"{date} · {source}" if date else source
        rows += f"""
        <a href="/entry/{i}" style="text-decoration:none;color:inherit;">
          <div class="card" style="padding:16px 20px;display:flex;align-items:center;justify-content:space-between;cursor:pointer;">
            <div>
              <div style="font-size:1rem;font-weight:400;margin-bottom:2px;letter-spacing:.5px;">{author}</div>
              <div style="color:var(--muted);font-size:.8rem;letter-spacing:.5px;">{meta}</div>
            </div>
            <div>{tag}</div>
          </div>
        </a>"""

    empty = "" if rows else """
    <div class="card" style="text-align:center;padding:64px;color:var(--muted);">
      <div style="font-size:2rem;margin-bottom:16px;">📜</div>
      <div style="font-size:1rem;font-weight:300;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;">Aucune entrée pour l'instant</div>
      <a href="/add" class="btn btn-primary">+ Ajouter une entrée</a>
    </div>"""

    content = f"""
    <div class="flex-between" style="margin-bottom:2rem;">
      <div>
        <h1 class="page-title">Collecte terrain</h1>
        <p class="page-sub">Validez et complétez chaque entrée scrapée depuis Wikipedia.</p>
      </div>
      <a href="/add" class="btn btn-primary">+ Ajouter</a>
    </div>
    <div class="card" style="margin-bottom:2rem;">
      <div class="flex-between">
        <div>
          <div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;">Progression globale</div>
          <div style="font-size:1.6rem;font-weight:300;margin-top:4px;">
            {validated} <span style="color:var(--muted);font-size:1rem;">/ {total} validées</span>
            &nbsp;<span style="color:var(--green);font-size:1rem;">{pct}%</span>
          </div>
        </div>
        <a href="/export" class="btn btn-secondary">↓ Exporter CSV</a>
      </div>
      <div class="progress-wrap"><div class="progress-fill" style="width:{pct}%;"></div></div>
    </div>
    {rows}{empty}"""

    return HTMLResponse(base(content, nav_collect="active"))

@app.get("/entry/{idx}", response_class=HTMLResponse)
async def edit_entry(idx: int):
    df = load_df()
    if idx < 0 or idx >= len(df):
        return RedirectResponse("/")
    row = df.iloc[idx]
    total = len(df)

    def val(field):
        v = str(row.get(field, "") or "")
        return v.replace('"', '&quot;').replace('<', '&lt;')

    is_val = bool(row.get("validated", False))
    tag = '<span class="tag-validated">✓ Validée</span>' if is_val else '<span class="tag-pending">À valider</span>'
    prev_btn = f'<a href="/entry/{idx-1}" class="btn btn-secondary">← Précédente</a>' if idx > 0 else ""
    next_btn = f'<a href="/entry/{idx+1}" class="btn btn-secondary">Suivante →</a>' if idx < total-1 else ""
    source_link = val("source_link")
    wiki = f'<div class="card" style="margin-top:20px;"><div style="font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Source</div><a href="{source_link}" target="_blank" style="color:var(--green);font-size:.85rem;">↗ Ouvrir sur Wikipedia</a></div>' if source_link else ""
    original_text = str(row.get("original_text", "") or "").replace('<', '&lt;').replace('>', '&gt;')

    content = f"""
    <div class="flex-between" style="margin-bottom:2rem;">
      <div>
        <a href="/" style="color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;">← Retour</a>
        <h1 class="page-title" style="margin-top:8px;">{val('author') or '(sans nom)'}</h1>
        <p class="page-sub">Entrée {idx+1} / {total}</p>
      </div>
      <div>{tag}</div>
    </div>
    <form method="post" action="/entry/{idx}/save">
      <div class="card">
        <div class="form-group"><label>Auteure</label><input type="text" name="author" value="{val('author')}"></div>
        <div class="grid2">
          <div class="form-group"><label>Date</label><input type="text" name="date" value="{val('date')}"></div>
          <div class="form-group"><label>Source</label><input type="text" name="source_name" value="{val('source_name')}"></div>
        </div>
        <div class="form-group"><label>Lien source</label><input type="text" name="source_link" value="{val('source_link')}"></div>
        <hr>
        <div class="form-group"><label>Texte original</label><textarea name="original_text">{original_text}</textarea></div>
      </div>
      <div class="flex" style="justify-content:space-between;margin-top:12px;">
        <div class="flex">{prev_btn}{next_btn}</div>
        <div class="flex">
          <button type="submit" class="btn btn-secondary">Sauvegarder</button>
          <button type="submit" name="do_validate" value="1" class="btn btn-success">✓ Valider & continuer</button>
        </div>
      </div>
    </form>
    {wiki}"""

    return HTMLResponse(base(content, nav_collect="active"))

@app.post("/entry/{idx}/save")
async def save_entry(
    idx: int,
    author: str = Form(""),
    original_text: str = Form(""),
    date: str = Form(""),
    source_name: str = Form(""),
    source_link: str = Form(""),
    do_validate: str = Form(None)
):
    df = load_df()
    df.at[idx, "author"] = author
    df.at[idx, "original_text"] = original_text
    df.at[idx, "date"] = date
    df.at[idx, "source_name"] = source_name
    df.at[idx, "source_link"] = source_link
    if do_validate:
        df.at[idx, "validated"] = True
    save_df(df)
    if do_validate:
        for i in range(idx + 1, len(df)):
            if not df.iloc[i]["validated"]:
                return RedirectResponse(f"/entry/{i}", status_code=303)
    return RedirectResponse("/", status_code=303)

@app.get("/add", response_class=HTMLResponse)
async def add_form():
    content = """
    <div style="margin-bottom:2rem;">
      <a href="/" style="color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;">← Retour</a>
      <h1 class="page-title" style="margin-top:8px;">Ajouter une entrée</h1>
      <p class="page-sub">Saisie manuelle d'une poétesse ou écrivaine médiévale.</p>
    </div>
    <form method="post" action="/add">
      <div class="card">
        <div class="form-group"><label>Auteure *</label><input type="text" name="author" required placeholder="Nom de l'auteure"></div>
        <div class="grid2">
          <div class="form-group"><label>Date</label><input type="text" name="date" placeholder="ex: XIIe siècle"></div>
          <div class="form-group"><label>Source</label><input type="text" name="source_name" placeholder="ex: Wikipedia"></div>
        </div>
        <div class="form-group"><label>Lien source</label><input type="text" name="source_link" placeholder="https://..."></div>
        <hr>
        <div class="form-group"><label>Texte original</label><textarea name="original_text" placeholder="Extrait ou biographie..."></textarea></div>
      </div>
      <div class="flex" style="justify-content:flex-end;margin-top:12px;gap:12px;">
        <a href="/" class="btn btn-secondary">Annuler</a>
        <button type="submit" class="btn btn-success">✓ Ajouter et valider</button>
      </div>
    </form>"""
    return HTMLResponse(base(content, nav_add="active"))

@app.post("/add")
async def add_entry(
    author: str = Form(""),
    original_text: str = Form(""),
    date: str = Form(""),
    source_name: str = Form(""),
    source_link: str = Form("")
):
    df = load_df()
    new_row = {"author": author, "original_text": original_text, "date": date,
               "source_name": source_name, "source_link": source_link, "validated": True}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_df(df)
    return RedirectResponse("/", status_code=303)

@app.get("/export")
async def export_csv():
    df = load_df()
    output = io.StringIO()
    df[FIELDS].to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=medieval_poetess_validated.csv"}
    )
