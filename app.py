import streamlit as st
import anthropic
import base64
import json
import difflib  # <--- INDISPENSABLE POUR LE MATCHING APPROXIMATIF
from datetime import datetime
import os

# ============================================
# 1. CONFIGURATION & STYLE
# ============================================
st.set_page_config(
    page_title="Dokii - Vérification Intelligente",
    page_icon="📄",
    layout="centered"
)

# CSS personnalisé - Dark Mode élégant
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #2c3e50 0%, #4A6274 50%, #34495e 100%);
        color: #E8E8E8;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, div, label { color: #E8E8E8 !important; }
    
    .dokii-title {
        font-family: 'Playfair Display', serif;
        font-size: 4.5rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -2px;
    }
    
    /* Boutons */
    .stButton > button {
        background-color: #E6DACE !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    .stButton > button:hover {
        background-color: #D4C4B8 !important;
        transform: translateY(-2px) !important;
    }
    div.stButton > button > div > p { color: #000000 !important; }
    
    /* Badges */
    .credit-badge {
        background: rgba(230, 218, 206, 0.15);
        border: 2px solid #E6DACE;
        border-radius: 20px;
        padding: 0.75rem 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .credit-number { font-size: 1.8rem; font-weight: 700; color: #E6DACE; }
    .credit-text { font-size: 0.85rem; color: #B8B8B8; margin-top: 0.25rem; }
    
    .trust-badge {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 1.25rem 0.75rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .trust-badge:hover { background: rgba(255, 255, 255, 0.12); transform: translateY(-3px); }
    .trust-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .trust-title { font-size: 0.95rem; font-weight: 600; color: #FFFFFF; }
    .trust-subtitle { font-size: 0.75rem; color: #B8B8B8; }
    
    /* Blocs */
    .block-container {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
    }
    .block-title { font-size: 1.8rem; font-weight: 700; color: #E6DACE; margin-bottom: 1rem; }
    
    /* Overrides */
    .stCheckbox { color: #E8E8E8; }
    .uploadedFile { background: rgba(230, 218, 206, 0.1) !important; border: 2px solid #E6DACE !important; border-radius: 15px !important; }
    .stAlert { border-radius: 15px !important; background: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; }
    .streamlit-expanderHeader { background: rgba(230, 218, 206, 0.1) !important; border-radius: 15px !important; color: #FFFFFF !important; }
    .stSpinner > div { border-top-color: #E6DACE !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. SESSION STATE & HELPERS
# ============================================
if 'consented' not in st.session_state:
    st.session_state.consented = False
if 'files_analyzed' not in st.session_state:
    st.session_state.files_analyzed = 0
if 'current_month' not in st.session_state:
    st.session_state.current_month = datetime.now().strftime("%Y-%m")
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

MONTHLY_LIMIT = 15
current_month = datetime.now().strftime("%Y-%m")

if st.session_state.current_month != current_month:
    st.session_state.files_analyzed = 0
    st.session_state.current_month = current_month

credits_remaining = MONTHLY_LIMIT - st.session_state.files_analyzed

def encode_file_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# ============================================
# 3. MOTEUR LOGIQUE (PYTHON + IA)
# ============================================

def verifier_coherence_python(data):
    """
    Logique Python hybride : 
    1. Utilise le Fuzzy Matching pour relier les noms approximatifs.
    2. Utilise les maths strictes pour calculer les écarts.
    """
    errors = []
    verification_positive = []
    
    docs = data.get('documents', [])
    commandes = [d for d in docs if d['type'] == 'commande']
    livraisons = [d for d in docs if d['type'] == 'livraison']
    
    if not commandes or not livraisons:
        return {
            "status": "error",
            "errors": [{"severity": "warning", "type": "Manquant", "description": "Il faut 1 Bon de Commande et 1 Bon de Livraison."}],
            "details": "Documents manquants.",
            "raw_data": data
        }

    cmd = commandes[0]
    liv = livraisons[0]
    
    # Création map des items livrés pour recherche rapide
    liv_items_map = {item['description']: item for item in liv['lignes']}
    liv_descriptions = list(liv_items_map.keys())

    # --- BOUCLE DE COMPARAISON ---
    for item_cmd in cmd['lignes']:
        nom_cmd = item_cmd['description']
        qty_cmd = float(item_cmd.get('quantite', 0))
        
        # 1. RECHERCHE INTELLIGENTE (FUZZY MATCH)
        # On cherche si un nom dans la livraison ressemble à celui de la commande (seuil 70%)
        match = difflib.get_close_matches(nom_cmd, liv_descriptions, n=1, cutoff=0.70)
        
        item_liv = None
        nom_liv_trouve = ""
        
        if match:
            nom_liv_trouve = match[0]
            item_liv = liv_items_map[nom_liv_trouve]
        
        # 2. ANALYSE DES ÉCARTS
        if item_liv:
            qty_liv = float(item_liv.get('quantite', 0))
            ecart = qty_liv - qty_cmd
            
            if ecart < 0:
                # ERREUR CRITIQUE (Manquant)
                errors.append({
                    "type": "Quantité (Manquant)",
                    "severity": "critique",
                    "description": f"Manque {abs(ecart)} unité(s).",
                    "article": f"{nom_cmd} (Sur BL: {nom_liv_trouve})",
                    "quantite_commandee": qty_cmd,
                    "quantite_livree": qty_liv,
                    "ecart": ecart,
                    "document1": "Commande", "document2": "Livraison",
                    "ligne_document1": item_cmd.get('ligne_pdf'),
                    "ligne_document2": item_liv.get('ligne_pdf')
                })
            elif ecart > 0:
                # WARNING (Surplus)
                errors.append({
                    "type": "Quantité (Surplus)",
                    "severity": "warning",
                    "description": "Reçu plus que commandé",
                    "article": nom_cmd,
                    "quantite_commandee": qty_cmd,
                    "quantite_livree": qty_liv,
                    "ecart": f"+{ecart}",
                    "document1": "Commande", "document2": "Livraison"
                })
            else:
                # C'EST TOUT BON
                verification_positive.append(f"OK : {nom_cmd}")
        else:
            # ERREUR : Article commandé mais TOTALEMENT ABSENT de la livraison
            errors.append({
                "type": "Non livré",
                "severity": "critique",
                "description": "Article présent sur la commande mais ABSENT du BL",
                "article": nom_cmd,
                "quantite_commandee": qty_cmd,
                "quantite_livree": 0,
                "ecart": -qty_cmd,
                "document1": "Commande", "document2": "Inexistant"
            })

    return {
        "status": "success" if not errors else "error",
        "errors": errors,
        "verification_positive": " | ".join(verification_positive),
        "details": f"Comparaison (Mode Fuzzy Match) entre {cmd.get('reference')} et {liv.get('reference')}.",
        "anomalies_count": len(errors),
        "raw_data": data 
    }

def analyze_documents(files):
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
        if not api_key:
            st.error("⚠️ Clé API Anthropic non configurée.")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        content = []
        for file in files:
            file_data = encode_file_to_base64(file)
            content.append({
                "type": "document",
                "source": { "type": "base64", "media_type": "application/pdf", "data": file_data }
            })
        
        # PROMPT RENFORCÉ POUR LES COLONNES PIÈGES (Reliquat vs Livré)
        prompt_text = """
        Tu es un expert en logistique. Analyse ces documents (Commandes et Livraisons).
        
        RÈGLE D'OR POUR LES BONS DE LIVRAISON (BL) :
        1. Sur un BL, il y a souvent plusieurs colonnes de quantité : "Commandé" (Cde), "Livré", "Reliquat".
        2. TU DOIS IMPÉRATIVEMENT EXTRAIRE LA VALEUR DE LA COLONNE "LIVRÉ".
        3. IGNORE la colonne "Commandé" ou "Reliquat" pour déterminer la quantité reçue.
        4. Si la colonne "Livré" est vide ou contient "0", la quantité extraite doit être 0.
        
        Exemple : Si "Cde"=78, "Livré"=0, "Reliquat"=78 -> Tu dois extraire quantité = 0.
        
        Renvoie UNIQUEMENT un JSON :
        {
            "documents": [
                {
                    "type": "commande" | "livraison",
                    "reference": "Ref Document",
                    "lignes": [
                        { "ligne_pdf": 1, "description": "Nom produit", "quantite": 10.0 }
                    ]
                }
            ]
        }
        """
        
        content.append({"type": "text", "text": prompt_text})
        
        # APPEL API (Température 0 pour la rigueur)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022", # Modèle le plus puissant
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": content}]
        )
        
        clean_text = message.content[0].text.replace("```json", "").replace("```", "").strip()
        data_extraite = json.loads(clean_text)
        
        # Appel de la logique Python
        return verifier_coherence_python(data_extraite)

    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        return None

# ============================================
# 4. INTERFACE UTILISATEUR (UI)
# ============================================

# HEADER
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h1 class="dokii-title">Dokii.</h1>', unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="credit-badge">
        <div class="credit-number">{credits_remaining}</div>
        <div class="credit-text">Crédits restants</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# BADGES CONFIANCE
trust_badges = [("🔒", "TLS", "Sécurisé"), ("🛡️", "RGPD", "Conforme"), ("🗑️", "Delete", "Auto"), ("👁️", "Privé", "Secret")]
cols = st.columns(4)
for col, (icon, title, subtitle) in zip(cols, trust_badges):
    with col:
        st.markdown(f"<div class='trust-badge'><div class='trust-icon'>{icon}</div><div class='trust-title'>{title}</div><div class='trust-subtitle'>{subtitle}</div></div>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

# BLOC 1 : CONSENTEMENT
st.markdown('<div class="block-container"><h2 class="block-title">🔐 1. Confidentialité</h2><p style="color:#D0D0D0">Analyse sécurisée et chiffrée.</p>', unsafe_allow_html=True)
consent_checkbox = st.checkbox("✓ Je confirme l'upload de documents non sensibles.", key="consent")
st.session_state.consented = consent_checkbox
st.markdown('</div><br>', unsafe_allow_html=True)

# BLOC 2 : UPLOAD
if st.session_state.consented:
    st.markdown('<div class="block-container"><h2 class="block-title">📂 2. Importez vos documents</h2>', unsafe_allow_html=True)
    
    if credits_remaining > 0:
        uploaded_files = st.file_uploader("Fichiers PDF", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")
        
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} fichier(s) prêt(s)**")
            for i, f in enumerate(uploaded_files, 1): st.markdown(f"📄 {f.name}")
            
            if st.button("⚡ Lancer l'analyse (V3)", use_container_width=True):
                with st.spinner("🧠 Lecture intelligente & Calculs en cours..."):
                    result = analyze_documents(uploaded_files)
                    if result:
                        st.session_state.files_analyzed += len(uploaded_files)
                        st.session_state.analysis_result = result
                        st.rerun()
    else:
        st.error("❌ Crédits épuisés.")
    st.markdown('</div><br>', unsafe_allow_html=True)

# BLOC 3 : RÉSULTATS
if st.session_state.consented and st.session_state.analysis_result:
    res = st.session_state.analysis_result
    st.markdown('<div class="block-container"><h2 class="block-title">📊 3. Résultat du Matching</h2>', unsafe_allow_html=True)
    
    if res['status'] == 'success':
        st.success("✅ **Tout correspond parfaitement !**")
    else:
        st.error(f"⚠️ **{len(res['errors'])} anomalie(s) détectée(s)**")
        
        # Afficher les erreurs
        for i, err in enumerate(res['errors'], 1):
            sev = "🔴" if err['severity'] == 'critique' else "🟠"
            with st.expander(f"{sev} {err['type']} - {err['article']}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Problème :** {err['description']}")
                    st.write(f"**Écart :** {err['ecart']}")
                with c2:
                    st.write(f"**Commandé :** {err['quantite_commandee']}")
                    st.write(f"**Reçu (Lu par IA) :** {err['quantite_livree']}")
                st.caption(f"Documents : {err.get('document1')} vs {err.get('document2')}")

    # DEBUG SECTION (Pour voir ce que l'IA a lu si besoin)
    with st.expander("🕵️‍♂️ Voir les données brutes (Debug)"):
        st.json(res.get('raw_data'))

    if st.button("🔄 Nouvelle analyse", use_container_width=True):
        st.session_state.analysis_result = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("<br><br><div style='text-align:center;color:#B8B8B8'>Dokii V3 • Powered by Claude 3.5 Sonnet</div>", unsafe_allow_html=True)
