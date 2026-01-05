import streamlit as st
import anthropic
import base64
import json
import difflib
import os

# ============================================
# 1. CONFIGURATION & STYLE
# ============================================
st.set_page_config(
    page_title="Dokii Pro - Analyse Illimitée",
    page_icon="🚀",
    layout="wide"  # Layout large pour mieux voir les tableaux
)

# CSS personnalisé - Dark Mode avec correction de lisibilité
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global App Style */
    .stApp {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Titres */
    h1, h2, h3 { color: #f1f5f9 !important; }
    
    .dokii-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(to right, #e2e8f0, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -1px;
    }
    
    /* Boutons */
    .stButton > button {
        background: linear-gradient(to right, #fbbf24, #d97706) !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(251, 191, 36, 0.5) !important;
    }
    div.stButton > button > div > p { color: #000000 !important; }
    
    /* Conteneurs (Blocs) */
    .block-container {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* CORRECTION CRITIQUE : Texte à l'intérieur des Expanders (Détails) 
       On force le texte en NOIR/GRIS FONCÉ quand c'est sur fond blanc */
    div[data-testid="stExpanderDetails"] {
        background-color: #f8fafc !important;
        border-radius: 0 0 10px 10px;
    }
    div[data-testid="stExpanderDetails"] p, 
    div[data-testid="stExpanderDetails"] span, 
    div[data-testid="stExpanderDetails"] div,
    div[data-testid="stExpanderDetails"] li { 
        color: #1e293b !important; /* Gris très foncé pour la lisibilité */
        font-size: 0.95rem;
    }
    
    /* Header de l'expander */
    .streamlit-expanderHeader {
        background-color: #334155 !important;
        color: #ffffff !important;
        border-radius: 10px;
        font-weight: 600;
    }

    /* Badges de statut */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 10px;
    }
    .badge-ok { background: #dcfce7; color: #166534; }
    .badge-error { background: #fee2e2; color: #991b1b; }
    
</style>
""", unsafe_allow_html=True)

# ============================================
# 2. SESSION STATE
# ============================================
if 'consented' not in st.session_state:
    st.session_state.consented = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

def encode_file_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# ============================================
# 3. MOTEUR LOGIQUE
# ============================================

def organiser_documents(docs_extraits):
    """
    Algorithme de regroupement intelligent.
    Trie les documents par 'Dossier' (basé sur le numéro de commande).
    """
    groupes = {}
    orphelins = []

    # 1. D'abord, on crée les groupes basés sur les Commandes
    for doc in docs_extraits:
        if doc['type'] == 'commande':
            ref = doc['reference']
            if ref not in groupes:
                groupes[ref] = {'commande': doc, 'livraisons': [], 'factures': []}
            else:
                # Cas rare : doublon de commande, on écrase ou on ignore
                groupes[ref]['commande'] = doc

    # 2. Ensuite, on range les BL et Factures
    for doc in docs_extraits:
        if doc['type'] == 'commande':
            continue
            
        # On regarde si le document cite une commande connue (lien fort)
        lien_trouve = False
        ref_liee = doc.get('reference_liee')
        
        # Nettoyage sommaire de la ref liée (ex: "Commande N°123" -> "123")
        if ref_liee:
            for ref_cmd in groupes.keys():
                if ref_cmd in ref_liee or ref_liee in ref_cmd:
                    if doc['type'] == 'livraison':
                        groupes[ref_cmd]['livraisons'].append(doc)
                    elif doc['type'] == 'facture':
                        groupes[ref_cmd]['factures'].append(doc)
                    lien_trouve = True
                    break
        
        # Si pas de lien trouvé via la réf, on le met en orphelin (ou on pourrait tenter un fuzzy match)
        if not lien_trouve:
            orphelins.append(doc)

    return groupes, orphelins

def verifier_coherence_groupe(groupe, ref_dossier):
    """
    Compare les documents au sein d'un même groupe (1 Commande vs N Livraisons).
    Génère un résumé textuel clair.
    """
    cmd = groupe.get('commande')
    livraisons = groupe.get('livraisons', [])
    
    if not cmd:
        return {
            "status": "warning", 
            "titre": f"Dossier {ref_dossier} (Incomplet)",
            "texte": "⚠️ Ce dossier contient des livraisons ou factures, mais **le Bon de Commande est manquant**. Impossible de vérifier les écarts."
        }
    
    if not livraisons:
        return {
            "status": "warning",
            "titre": f"Dossier {ref_dossier} (Commande seule)",
            "texte": f"ℹ️ Bon de commande présent ({len(cmd['lignes'])} articles), mais **aucun Bon de Livraison** associé n'a été trouvé."
        }

    # Préparation de l'analyse
    erreurs = []
    points_positifs = []
    
    # On aggrège toutes les livraisons (cas où une commande est livrée en 2 fois)
    # Map: Description -> {quantite_recue: X, prix: Y}
    total_livre = {}
    
    # Noms des BL pour le rapport
    refs_bl = [l['reference'] for l in livraisons]
    noms_bl_str = ", ".join(refs_bl)

    # Remplissage map livraison (Fuzzy match possible ici si besoin, pour l'instant strict + simple normalisation)
    for liv in livraisons:
        for ligne in liv['lignes']:
            desc = ligne['description']
            qty = float(ligne.get('quantite', 0))
            if desc in total_livre:
                total_livre[desc] += qty
            else:
                total_livre[desc] = qty

    # --- Comparaison Commande vs Total Livré ---
    items_livraison_keys = list(total_livre.keys())
    
    for item_cmd in cmd['lignes']:
        nom_cmd = item_cmd['description']
        qty_cmd = float(item_cmd.get('quantite', 0))
        
        # Fuzzy Match pour retrouver le produit dans le vrac de livraison
        match = difflib.get_close_matches(nom_cmd, items_livraison_keys, n=1, cutoff=0.7)
        
        qty_recue = 0
        trouve = False
        nom_trouve = ""
        
        if match:
            nom_trouve = match[0]
            qty_recue = total_livre[nom_trouve]
            trouve = True
        
        ecart = qty_recue - qty_cmd
        
        if ecart < 0:
            erreurs.append(f"❌ **{nom_cmd}** : Commandé {qty_cmd} / Reçu {qty_recue} (Manque {abs(ecart)})")
        elif ecart > 0:
            erreurs.append(f"⚠️ **{nom_cmd}** : Commandé {qty_cmd} / Reçu {qty_recue} (Surplus {ecart})")
        else:
            # Si quantité OK, on ne spamme pas, on note juste que c'est bon
            pass

    # Génération du rapport narratif
    if not erreurs:
        texte_resume = f"""
        **Tout est parfait sur ce dossier.**
        
        Les documents analysés (Commande {cmd['reference']} et Livraison(s) {noms_bl_str}) correspondent parfaitement.
        
        ✅ **Quantités :** Les {len(cmd['lignes'])} articles commandés ont tous été livrés en quantité exacte.
        ✅ **Références :** Les produits correspondent bien entre le bon de commande et le bon de réception.
        """
        status = "success"
    else:
        nb_err = len(erreurs)
        texte_resume = f"""
        **Attention, nous avons détecté {nb_err} anomalie(s) sur ce dossier.**
        
        Comparaison effectuée entre la **Commande {cmd['reference']}** et **Livraison(s) {noms_bl_str}**.
        
        Voici le détail des problèmes :
        
        {chr(10).join(erreurs)}
        
        ---
        *Les autres articles non listés ici sont conformes.*
        """
        status = "error"

    return {
        "status": status,
        "titre": f"Dossier {ref_dossier}",
        "texte": texte_resume,
        "raw_erreurs": erreurs
    }

def analyze_documents(files):
    try:
        # -----------------------------------------------------------
        # CLÉ API : Remplace ci-dessous ou utilise secrets.toml
        # -----------------------------------------------------------
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
        if not api_key:
            st.error("⚠️ Clé API non trouvée.")
            return None
            
        client = anthropic.Anthropic(api_key=api_key)
        
        # Préparation des images
        content_messages = []
        for file in files:
            file_data = encode_file_to_base64(file)
            content_messages.append({
                "type": "document",
                "source": { "type": "base64", "media_type": "application/pdf", "data": file_data }
            })
            
        # -----------------------------------------------------------
        # PROMPT D'EXTRACTION (Avec détection de liens entre docs)
        # -----------------------------------------------------------
        prompt_extraction = """
        Tu es un assistant expert en logistique. J'ai uploadé plusieurs documents en vrac (Commandes, BL, Factures).
        
        TA MISSION : Extraire les données de CHAQUE document pour que je puisse ensuite les trier.
        
        RÈGLES D'OR POUR L'EXTRACTION :
        1. **Type & Référence** : Identifie le type (commande/livraison/facture) et la référence du document LUI-MÊME.
        2. **Lien de parenté** : C'EST LE PLUS IMPORTANT. Sur un BL ou une Facture, cherche la référence de la COMMANDE d'origine (ex: "Ref Cde Client: 450", "Votre commande N° BC-22"). Extrais-le dans le champ 'reference_liee'.
        3. **Quantités BL (Le Piège)** : Sur un Bon de Livraison, ignore les colonnes "Commandé" ou "Reliquat". Extrais UNIQUEMENT la valeur dans la colonne "LIVRÉ" ou "QTÉ LIVRÉE". Si vide ou 0, mets 0.
        
        Renvoie un JSON unique contenant une liste de tous les documents :
        {
          "documents": [
            {
              "type": "commande" | "livraison" | "facture",
              "reference": "N° du document (ex: BL-2025-01)",
              "reference_liee": "N° de la commande citée (ex: BC-2025-01)", 
              "lignes": [
                { "description": "Nom produit", "quantite": 12.0, "prix": 0.0 }
              ]
            }
          ]
        }
        """
        
        content_messages.append({"type": "text", "text": prompt_extraction})
        
        # Appel API (Claude 3.5 Sonnet)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000, # Augmenté pour gérer 30 docs
            temperature=0,
            messages=[{"role": "user", "content": content_messages}]
        )
        
        # Parsing
        clean_text = message.content[0].text.replace("```json", "").replace("```", "").strip()
        data_brute = json.loads(clean_text)
        
        # --- LOGIQUE PYTHON : CLUSTERING & VERIF ---
        docs = data_brute.get('documents', [])
        groupes, orphelins = organiser_documents(docs)
        
        resultats_finaux = []
        
        # Analyse de chaque groupe identifié
        for ref_cmd, groupe in groupes.items():
            analyse = verifier_coherence_groupe(groupe, ref_cmd)
            resultats_finaux.append(analyse)
            
        # Gestion des orphelins (docs qu'on n'a pas su relier)
        if orphelins:
            txt_orphelins = "\n".join([f"- {d['type']} {d['reference']}" for d in orphelins])
            resultats_finaux.append({
                "status": "info",
                "titre": "Documents non reliés",
                "texte": f"Certains documents n'ont pas pu être rattachés automatiquement à un dossier :\n{txt_orphelins}"
            })
            
        return resultats_finaux

    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        return None

# ============================================
# 4. INTERFACE UI
# ============================================

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<h1 class="dokii-title">Dokii Pro.</h1>', unsafe_allow_html=True)
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    # Plus de limite affichée, juste un badge Pro
    st.markdown('<div class="status-badge" style="background:#fbbf24; color:black; font-size:1rem; padding:10px 20px;">⚡ VERSION ILLIMITÉE</div>', unsafe_allow_html=True)

st.markdown("---")

# CONSENTEMENT
if not st.session_state.consented:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("### 🔒 Confidentialité & Sécurité")
    st.info("Vos documents sont traités par IA sécurisée et ne sont pas conservés.")
    if st.checkbox("Je confirme l'upload de documents professionnels."):
        st.session_state.consented = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# UPLOAD
if st.session_state.consented:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown("### 📂 Import Multi-Dossiers")
    st.markdown("Vous pouvez charger **30 documents ou plus** (Commandes, BL, Factures) mélangés. Dokii va les trier par dossier.")
    
    uploaded_files = st.file_uploader(
        "Glissez vos PDF ici", 
        type=['pdf'], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} documents chargés.")
        
        if st.button("Lancer l'Analyse Groupée", use_container_width=True):
            with st.spinner("🤖 Dokii trie vos dossiers et vérifie les quantités..."):
                res = analyze_documents(uploaded_files)
                st.session_state.analysis_results = res
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# RESULTATS
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    
    st.markdown("## 📊 Rapport d'Analyse")
    
    for res in results:
        # Définition de la couleur de l'entête selon le statut
        icon = "✅"
        if res['status'] == 'error': icon = "🔴"
        elif res['status'] == 'warning': icon = "🟠"
        elif res['status'] == 'info': icon = "ℹ️"
        
        with st.expander(f"{icon} {res['titre']}", expanded=(res['status']=='error')):
            # Le Markdown ici sera automatiquement formaté en noir grâce au CSS ajouté
            st.markdown(res['texte'])

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Nouvelle Analyse"):
        st.session_state.analysis_results = None
        st.rerun()
