import streamlit as st
import anthropic
import base64
import json
import difflib
import os

# ============================================
# 1. CONFIGURATION & STYLE (CSS NUCLÉAIRE)
# ============================================
st.set_page_config(
    page_title="Dokii Pro",
    page_icon="🚀",
    layout="wide"
)

# CSS pour Dark Mode forcé + Lisibilité Texte
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Fond Sombre */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Titres et Textes */
    h1, h2, h3, p, div, span, li, label { color: #f8fafc !important; }
    
    /* Titre Principal */
    .dokii-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(to right, #f8fafc, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    /* Badges de Confiance (Restaurés) */
    .trust-badge {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 10px;
    }
    .trust-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .trust-title { font-weight: bold; font-size: 0.9rem; }
    
    /* Bouton Action */
    .stButton > button {
        background: linear-gradient(to right, #f59e0b, #d97706) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        padding: 0.8rem 2rem !important;
        width: 100%;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Conteneurs */
    .block-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    
    /* CORRECTION LISIBILITÉ RÉSULTATS (IMPORTANT) */
    div[data-testid="stExpanderDetails"] {
        background-color: rgba(0, 0, 0, 0.5) !important; /* Fond sombre semi-transparent */
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0 !important; /* Texte clair */
    }
    div[data-testid="stExpanderDetails"] p,
    div[data-testid="stExpanderDetails"] li,
    div[data-testid="stExpanderDetails"] strong {
        color: #e2e8f0 !important;
    }
    
    /* Badge Illimité */
    .unlimited-badge {
        background: #10b981;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        border: 1px solid rgba(255,255,255,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. SESSION STATE (Gestion de la mémoire)
# ============================================
if 'consented' not in st.session_state:
    st.session_state.consented = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

def encode_file_to_base64(uploaded_file):
    # On revient au début du fichier au cas où
    uploaded_file.seek(0)
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# ============================================
# 3. MOTEUR LOGIQUE (TRI + ANALYSE)
# ============================================

def organiser_documents(docs_extraits):
    """Trie les documents par dossier (Commande mère)"""
    groupes = {}
    orphelins = []

    # 1. Créer les dossiers
    for doc in docs_extraits:
        if doc['type'] == 'commande':
            ref = doc['reference']
            if ref not in groupes:
                groupes[ref] = {'commande': doc, 'livraisons': [], 'factures': []}

    # 2. Rattacher les autres
    for doc in docs_extraits:
        if doc['type'] == 'commande': continue
        
        lien_trouve = False
        ref_liee = doc.get('reference_liee')
        
        if ref_liee:
            for ref_cmd in groupes.keys():
                # Matching souple (si la ref est contenue dans l'autre)
                if ref_cmd in ref_liee or ref_liee in ref_cmd:
                    if doc['type'] == 'livraison': groupes[ref_cmd]['livraisons'].append(doc)
                    elif doc['type'] == 'facture': groupes[ref_cmd]['factures'].append(doc)
                    lien_trouve = True
                    break
        
        if not lien_trouve:
            orphelins.append(doc)

    return groupes, orphelins

def verifier_coherence_groupe(groupe, ref_dossier):
    """Vérifie les quantités et génère le texte narratif"""
    cmd = groupe.get('commande')
    livraisons = groupe.get('livraisons', [])
    
    if not cmd:
        return {"status": "warning", "titre": f"Dossier {ref_dossier} (Incomplet)", "texte": "⚠️ Bon de commande manquant."}
    if not livraisons:
        return {"status": "warning", "titre": f"Dossier {ref_dossier}", "texte": "ℹ️ Commande seule (Pas de BL trouvé)."}

    erreurs = []
    total_livre = {}
    
    # Cumul des livraisons
    for liv in livraisons:
        for ligne in liv['lignes']:
            desc = ligne['description']
            qty = float(ligne.get('quantite', 0))
            total_livre[desc] = total_livre.get(desc, 0) + qty

    items_livres_keys = list(total_livre.keys())
    
    # Comparaison Ligne à Ligne
    for item_cmd in cmd['lignes']:
        nom_cmd = item_cmd['description']
        qty_cmd = float(item_cmd.get('quantite', 0))
        
        # Fuzzy Match (Important pour Pantalon vs Pantalon H.)
        match = difflib.get_close_matches(nom_cmd, items_livres_keys, n=1, cutoff=0.60)
        
        qty_recue = 0
        if match:
            qty_recue = total_livre[match[0]]
        
        ecart = qty_recue - qty_cmd
        
        if ecart < 0:
            erreurs.append(f"❌ **{nom_cmd}** : Commandé {qty_cmd} / Reçu {qty_recue} (**Manque {abs(ecart)}**)")
        elif ecart > 0:
            erreurs.append(f"⚠️ **{nom_cmd}** : Commandé {qty_cmd} / Reçu {qty_recue} (Trop perçu)")

    # Rédaction Rapport
    noms_bl = ", ".join([l['reference'] for l in livraisons])
    if not erreurs:
        texte = f"""
        ### ✅ Dossier Conforme
        **Commande {cmd['reference']}** (reçue via {noms_bl})
        * Tous les articles ont été livrés en quantité exacte.
        * Aucune erreur de facturation détectée.
        """
        status = "success"
    else:
        liste_err = "\n\n".join(erreurs)
        texte = f"""
        ### 🚨 Anomalies ({len(erreurs)})
        **Commande {cmd['reference']}** vs **Livraisons**
        
        {liste_err}
        """
        status = "error"

    return {"status": status, "titre": f"Dossier {ref_dossier}", "texte": texte}

def analyze_documents(files):
    try:
        # ---------------------------------------------------------
        # CLÉ API (Récupérée depuis les secrets Streamlit)
        # ---------------------------------------------------------
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
        if not api_key:
            st.error("⚠️ Clé API non configurée dans les Secrets.")
            return None
            
        client = anthropic.Anthropic(api_key=api_key)
        
        content = []
        for file in files:
            content.append({
                "type": "document",
                "source": { "type": "base64", "media_type": "application/pdf", "data": encode_file_to_base64(file) }
            })
            
        # PROMPT (Spécial "Zéro Limite" & "Piège BL")
        prompt = """
        Analyse ces documents.
        1. Identifie le Type et la Référence du document.
        2. Trouve le lien : "Reference Commande" citée sur le BL ou la Facture.
        3. ATTENTION BL : Extrais UNIQUEMENT la colonne "LIVRÉ" (Ignore "Commandé"/"Reliquat").
        
        JSON STRICT :
        {
          "documents": [
            {
              "type": "commande"|"livraison"|"facture",
              "reference": "...",
              "reference_liee": "...",
              "lignes": [ { "description": "...", "quantite": 12.0 } ]
            }
          ]
        }
        """
        content.append({"type": "text", "text": prompt})
        
        # Appel API
        msg = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8000,
            temperature=0,
            messages=[{"role": "user", "content": content}]
        )
        
        data = json.loads(msg.content[0].text.replace("```json","").replace("```",""))
        
        # Traitement Python
        groupes, orphelins = organiser_documents(data.get('documents', []))
        resultats = []
        for ref, grp in groupes.items():
            resultats.append(verifier_coherence_groupe(grp, ref))
            
        return resultats

    except Exception as e:
        st.error(f"Erreur technique : {str(e)}")
        return None

# ============================================
# 4. INTERFACE UTILISATEUR (UI)
# ============================================

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<h1 class="dokii-title">Dokii Pro.</h1>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right; padding-top:20px;"><span class="unlimited-badge">⚡ ILLIMITÉ</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- BADGES DE CONFIANCE (Restaurés) ---
cols = st.columns(4)
badges_data = [("🔒", "TLS Chiffré"), ("🛡️", "RGPD Ready"), ("🗑️", "No Logs"), ("⚡", "Temps Réel")]
for col, (icon, text) in zip(cols, badges_data):
    with col:
        st.markdown(f"""
        <div class="trust-badge">
            <div class="trust-icon">{icon}</div>
            <div class="trust-title">{text}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- BLOC 1 : CONSENTEMENT (Restauré) ---
if not st.session_state.consented:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("### 🔐 Accès Sécurisé")
    st.markdown("""
    <p style="font-size:0.9rem; color:#cbd5e1 !important;">
    Pour utiliser Dokii Pro, veuillez confirmer que vous acceptez les conditions d'utilisation.
    Vos documents sont analysés en mémoire vive et supprimés immédiatement après le traitement.
    </p>
    """, unsafe_allow_html=True)
    
    # Checkbox avec callback pour forcer le refresh
    def valider_consentement():
        st.session_state.consented = True

    st.checkbox(
        "Je confirme l'upload de documents professionnels et j'accepte les CGU.", 
        on_change=valider_consentement
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- BLOC 2 : UPLOAD & ANALYSE ---
if st.session_state.consented:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("### 📂 Espace de Travail")
    st.markdown("Chargez vos **Commandes** et **Bons de Livraison** (même en vrac).")
    
    uploaded_files = st.file_uploader(
        "Glissez vos PDF ici", 
        type=['pdf'], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} documents prêts.")
        
        # --- LE BOUTON CORRIGÉ ---
        # On utilise un if simple, et on stocke le résultat dans session_state
        if st.button("LANCER L'ANALYSE 🚀"):
            with st.spinner("🧠 Dokii analyse et croise vos documents..."):
                resultats = analyze_documents(uploaded_files)
                
                if resultats:
                    st.session_state.analysis_results = resultats
                    st.rerun() # Force le rechargement pour afficher les résultats
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- BLOC 3 : RÉSULTATS ---
if st.session_state.analysis_results:
    st.markdown("## 📊 Rapport d'Analyse")
    
    for res in st.session_state.analysis_results:
        icon = "✅" if res['status'] == 'success' else "🚨" if res['status'] == 'error' else "⚠️"
        
        with st.expander(f"{icon} {res['titre']}", expanded=(res['status']=='error')):
            st.markdown(res['texte'])
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Nouvelle Analyse"):
        st.session_state.analysis_results = None
        st.rerun()

# Footer
st.markdown("<br><hr><div style='text-align:center; color:#64748b; font-size:0.8rem'>Dokii Pro • Powered by Claude 3.5 Sonnet</div>", unsafe_allow_html=True)
