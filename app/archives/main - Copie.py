from fastapi import FastAPI, Request, Form
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

def base(content: str, nav_collect="", nav_add="") -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Medieval Poetess — Collecte</title>
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1410;--parchment:#f5f0e8;--parchment-dark:#ede5d0;--rust:#8b3a2a;--rust-light:#c4533f;--gold:#b8860b;--muted:#6b5e4e;--border:#c9b99a;--validated:#2d5a3d;--validated-bg:#eaf3ec;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--parchment);color:var(--ink);font-family:'Inter',sans-serif;font-size:14px;min-height:100vh;}}
header{{background:var(--ink);color:var(--parchment);padding:0 32px;display:flex;align-items:center;justify-content:space-between;height:56px;border-bottom:3px solid var(--rust);}}
.logo{{font-family:'IM Fell English',serif;font-size:20px;color:var(--parchment);text-decoration:none;}}
.logo span{{color:var(--gold);}}
nav a{{color:var(--parchment);text-decoration:none;margin-left:24px;font-size:13px;opacity:0.75;}}
nav a:hover{{opacity:1;}}
nav a.active{{opacity:1;border-bottom:2px solid var(--rust-light);padding-bottom:2px;}}
.container{{max-width:960px;margin:0 auto;padding:32px 24px;}}
.page-title{{font-family:'IM Fell English',serif;font-size:28px;margin-bottom:6px;}}
.page-sub{{color:var(--muted);font-size:13px;margin-bottom:28px;}}
.btn{{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:4px;font-size:13px;font-weight:500;cursor:pointer;border:none;text-decoration:none;}}
.btn-primary{{background:var(--rust);color:white;}}
.btn-primary:hover{{background:var(--rust-light);}}
.btn-secondary{{background:var(--parchment-dark);color:var(--ink);border:1px solid var(--border);}}
.btn-success{{background:var(--validated);color:white;}}
.card{{background:white;border:1px solid var(--border);border-radius:6px;padding:24px;margin-bottom:16px;}}
.progress-bar-wrap{{background:var(--parchment-dark);border-radius:99px;height:8px;overflow:hidden;margin:10px 0 4px;}}
.progress-bar-fill{{height:100%;background:var(--validated);border-radius:99px;}}
.tag-validated{{display:inline-block;background:var(--validated-bg);color:var(--validated);border:1px solid #b3d9bc;border-radius:99px;padding:2px 10px;font-size:11px;font-weight:600;}}
.tag-pending{{display:inline-block;background:#fdf6e3;color:var(--gold);border:1px solid #e0c97a;border-radius:99px;padding:2px 10px;font-size:11px;font-weight:600;}}
label{{display:block;font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;}}
input[type=text],textarea{{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:4px;font-family:'Inter',sans-serif;font-size:14px;background:var(--parchment);color:var(--ink);}}
input[type=text]:focus,textarea:focus{{outline:none;border-color:var(--rust);background:white;}}
textarea{{min-height:120px;resize:vertical;}}
.form-group{{margin-bottom:18px;}}
hr{{border:none;border-top:1px solid var(--border);margin:24px 0;}}
.flex{{display:flex;gap:12px;align-items:center;}}
.flex-between{{display:flex;justify-content:space-between;align-items:center;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
</style>
</head>
<body>
<header>
  <a href="/" class="logo">✦ Medieval <span>Poetess</span></a>
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
              <div style="font-family:'IM Fell English',serif;font-size:16px;margin-bottom:2px;">{author}</div>
              <div style="color:var(--muted);font-size:12px;">{meta}</div>
            </div>
            <div>{tag}</div>
          </div>
        </a>"""

    empty = "" if rows else """
    <div class="card" style="text-align:center;padding:48px;color:var(--muted);">
      <div style="font-size:32px;margin-bottom:12px;">📜</div>
      <div style="font-family:'IM Fell English',serif;font-size:18px;margin-bottom:8px;">Aucune entrée pour l'instant</div>
      <a href="/add" class="btn btn-primary">+ Ajouter une entrée</a>
    </div>"""

    content = f"""
    <div class="flex-between" style="margin-bottom:28px;">
      <div>
        <h1 class="page-title">Collecte terrain</h1>
        <p class="page-sub">Validez et complétez chaque entrée scrapée depuis Wikipedia.</p>
      </div>
      <a href="/add" class="btn btn-primary">+ Ajouter manuellement</a>
    </div>
    <div class="card" style="margin-bottom:28px;">
      <div class="flex-between">
        <div>
          <div style="font-size:13px;color:var(--muted);">Progression globale</div>
          <div style="font-size:22px;font-family:'IM Fell English',serif;margin-top:2px;">
            {validated} / {total} validées &nbsp;·&nbsp; <span style="color:var(--validated);">{pct}%</span>
          </div>
        </div>
        <a href="/export" class="btn btn-secondary">↓ Exporter CSV</a>
      </div>
      <div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:{pct}%;"></div></div>
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
    wiki_link = f'<div class="card" style="margin-top:24px;"><div style="font-size:12px;color:var(--muted);margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Source Wikipedia</div><a href="{source_link}" target="_blank" style="color:var(--rust);font-size:13px;">↗ Ouvrir la page Wikipedia</a></div>' if source_link else ""

    original_text = str(row.get("original_text", "") or "").replace('<', '&lt;').replace('>', '&gt;')

    content = f"""
    <div class="flex-between" style="margin-bottom:24px;">
      <div>
        <a href="/" style="color:var(--muted);text-decoration:none;font-size:13px;">← Retour à la liste</a>
        <h1 class="page-title" style="margin-top:6px;">{val('author') or '(sans nom)'}</h1>
        <p class="page-sub">Entrée {idx+1} sur {total}</p>
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
      <div class="flex" style="justify-content:space-between;margin-top:8px;">
        <div class="flex">{prev_btn}{next_btn}</div>
        <div class="flex">
          <button type="submit" class="btn btn-secondary">Sauvegarder</button>
          <button type="submit" name="do_validate" value="1" class="btn btn-success">✓ Valider & continuer</button>
        </div>
      </div>
    </form>
    {wiki_link}"""

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
    <div style="margin-bottom:24px;">
      <a href="/" style="color:var(--muted);text-decoration:none;font-size:13px;">← Retour à la liste</a>
      <h1 class="page-title" style="margin-top:6px;">Ajouter une entrée</h1>
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
      <div class="flex" style="justify-content:flex-end;margin-top:8px;">
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
