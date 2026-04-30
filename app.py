import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Viaggi Smart DB", layout="wide", page_icon="🧳")

# --- GESTIONE DATABASE ---
def init_db():
    conn = sqlite3.connect('viaggi.db', check_same_thread=False)
    c = conn.cursor()
    # Creazione tabella se non esiste
    c.execute('''CREATE TABLE IF NOT EXISTS checklist 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  categoria TEXT, 
                  item TEXT, 
                  fatto INTEGER)''')
    
    # Inserimento dati iniziali solo se il DB è vuoto
    c.execute("SELECT COUNT(*) FROM checklist")
    if c.fetchone()[0] == 0:
        default_items = [
            ("DOCUMENTI", "Documento identità", 0), ("DOCUMENTI", "Patente", 0),
            ("ELETTRONICA", "Smartphone", 0), ("ELETTRONICA", "Powerbank", 0),
            ("ABBIGLIAMENTO", "T-shirt", 0), ("ABBIGLIAMENTO", "Intimo", 0),
            ("IGIENE", "Spazzolino", 0), ("EXTRA", "Snack", 0)
        ]
        c.executemany("INSERT INTO checklist (categoria, item, fatto) VALUES (?, ?, ?)", default_items)
        conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- FUNZIONI CRUD ---
def add_item(cat, text):
    c.execute("INSERT INTO checklist (categoria, item, fatto) VALUES (?, ?, 0)", (cat, text))
    conn.commit()

def toggle_item(id_item, current_state):
    new_state = 1 if current_state == 0 else 0
    c.execute("UPDATE checklist SET fatto = ? WHERE id = ?", (new_state, id_item))
    conn.commit()

def delete_item(id_item):
    c.execute("DELETE FROM checklist WHERE id = ?", (id_item,))
    conn.commit()

def update_text(id_item, new_text):
    c.execute("UPDATE checklist SET item = ? WHERE id = ?", (new_text, id_item))
    conn.commit()

# --- INTERFACCIA UTENTE ---
st.title("🧳 Viaggi Smart Dashboard")

# Sidebar per aggiunta nuovi oggetti
with st.sidebar:
    st.header("➕ Nuovo Oggetto")
    new_cat = st.selectbox("Categoria", ["DOCUMENTI", "ELETTRONICA", "ABBIGLIAMENTO", "IGIENE", "SPIAGGIA", "EXTRA"])
    new_text = st.text_input("Cosa aggiungere?")
    if st.button("Aggiungi alla lista"):
        if new_text:
            add_item(new_cat, new_text)
            st.rerun()

# --- DASHBOARD & REPORT ---
df = pd.read_sql_query("SELECT * FROM checklist", conn)
total = len(df)
fatti = len(df[df['fatto'] == 1])
mancanti = total - fatti
progres_perc = int((fatti / total) * 100) if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Totale", total)
col2.metric("Completati", fatti, delta=fatti, delta_color="normal")
col3.metric("Mancanti", mancanti, delta=-mancanti, delta_color="inverse")

st.progress(progres_perc / 100)
st.write(f"Progresso valigia: **{progres_perc}%**")

# --- LISTA MODIFICABILE ---
st.divider()
tabs = st.tabs(["📝 Checklist", "⚙️ Gestisci Elenco"])

with tabs[0]:
    # Vista Utente (Checklist rapida)
    categories = df['categoria'].unique()
    for cat in categories:
        st.subheader(f"{cat}")
        cat_items = df[df['categoria'] == cat]
        for _, row in cat_items.iterrows():
            checked = st.checkbox(row['item'], value=row['fatto'] == 1, key=f"check_{row['id']}")
            if checked != (row['fatto'] == 1):
                toggle_item(row['id'], row['fatto'])
                st.rerun()

with tabs[1]:
    # Vista Admin (Modifica ed eliminazione)
    st.write("Modifica o elimina le voci esistenti:")
    for _, row in df.iterrows():
        col_text, col_edit, col_del = st.columns([3, 1, 1])
        with col_text:
            new_val = st.text_input(f"Edit {row['id']}", value=row['item'], label_visibility="collapsed", key=f"input_{row['id']}")
            if new_val != row['item']:
                update_text(row['id'], new_val)
                st.rerun()
        with col_edit:
            st.info(row['categoria'])
        with col_del:
            if st.button("🗑️", key=f"del_{row['id']}"):
                delete_item(row['id'])
                st.rerun()
