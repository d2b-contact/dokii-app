import streamlit as st
import anthropic
import base64
import json
import os

# Configuration de la page
st.set_page_config(
    page_title="Dokii - Vérification Intelligente",
    page_icon="📄",
    layout="centered"
)

# CSS personnalisé - Dark Mode moderne et épuré
st.markdown("""
<style>
    /* Import Google Fonts - Police moderne */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Background principal - Noir moderne doux */
    .stApp {
        background: #0a0a0a;
        color: #FFFFFF;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Tous les textes en blanc */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #FFFFFF !important;
    }
    
    /* Titre principal "Dokii" - Moderne et élégant */
    .dokii-title {
        font-family: 'Inter', sans-serif;
        font-size: 4.5rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -3px;
        background: linear-gradient(135deg, #FFFFFF 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Boutons modernes - Gradient électrique */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.875rem 2.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%) !important;
        color: #666666 !important;
        box-shadow: none !important;
    }
    
    /* Forcer la couleur du texte dans les boutons */
    div.stButton > button > div > p {
        color: #FFFFFF !important;
    }
    
    div.stButton > button:hover > div > p {
        color: #FFFFFF !important;
    }
    
    /* Badges de confiance - Design épuré */
    .trust-badge {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .trust-badge:hover {
        background: #222222;
        border-color: #667eea;
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
    }
    
    .trust-icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
        filter: grayscale(0%);
    }
    
    .trust-title {
        font-size: 1rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: 0.5px;
    }
    
    .trust-subtitle {
        font-size: 0.75rem;
        color: #888888;
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Conteneurs de blocs - Cards modernes */
    .block-container {
        background: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 20px;
        padding: 2.5rem;
        margin: 2rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    .block-title {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        letter-spacing: -0.5px;
    }
    
    /* Checkbox moderne */
    .stCheckbox {
        font-size: 1rem;
        color: #FFFFFF;
    }
    
    .stCheckbox > label {
        color: #FFFFFF !important;
    }
    
    /* File uploader - Design moderne */
    .uploadedFile {
        background: #1a1a1a !important;
        border: 2px solid #2a2a2a !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #667eea !important;
        background: #1f1f1f !important;
    }
    
    .uploadedFile label {
        color: #FFFFFF !important;
    }
    
    /* Texte dans les messages */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #FFFFFF !important;
    }
    
    /* Progress bar moderne */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 10px;
    }
    
    /* Messages d'alerte - Design moderne */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    
    /* Success message */
    .stSuccess {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
    }
    
    .stSuccess > div {
        color: #FFFFFF !important;
    }
    
    /* Error message */
    .stError {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3);
    }
    
    .stError > div {
        color: #FFFFFF !important;
    }
    
    /* Info message */
    .stInfo {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
    }
    
    .stInfo > div {
        color: #FFFFFF !important;
    }
    
    /* Warning message */
    .stWarning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
    }
    
    .stWarning > div {
        color: #FFFFFF !important;
    }
    
    /* Expander - Design épuré */
    .streamlit-expanderHeader {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #222222 !important;
        border-color: #667eea !important;
    }
    
    .streamlit-expanderContent {
        background: #141414 !important;
        border: 1px solid #2a2a2a !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.5rem !important;
    }
    
    /* Metrics - Design moderne */
    .stMetric {
        background: #1a1a1a;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #2a2a2a;
    }
    
    .stMetric > div > div {
        color: #FFFFFF !important;
    }
    
    /* Divider élégant */
    hr {
        border-color: #2a2a2a !important;
        margin: 2rem 0 !important;
    }
    
    /* Spinner moderne */
    .stSpinner > div {
        border-top-color: #667eea !important;
        border-right-color: #764ba2 !important;
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2a2a2a;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3a3a3a;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 8px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 1px #667eea !important;
    }
    
    /* Links */
    a {
        color: #667eea !important;
        text-decoration: none;
    }
    
    a:hover {
        color: #764ba2 !important;
        text-decoration: underline;
    }
    
    /* Dataframes */
    .dataframe {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 12px !important;
    }
    
    .dataframe th {
        background: #222222 !important;
        color: #FFFFFF !important;
    }
    
    .dataframe td {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du session state
if 'consented' not in st.session_state:
    st.session_state.consented = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Fonction pour encoder un fichier en base64
def encode_file_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# Fonction pour analyser les documents avec Claude
def analyze_documents(files):
    try:
        # Récupérer la clé API depuis les secrets ou variables d'environnement
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
        
        if not api_key:
            st.error("⚠️ Clé API Anthropic non configurée.")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Préparer les documents pour l'API
        content = []
        for file in files:
            file_data = encode_file_to_base64(file)
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": file_data
                }
            })
        
        # Ajouter le prompt amélioré
        content.append({
            "type": "text",
            "text": """Analyse ces documents et vérifie la cohérence entre bons de commande, bons de livraison et factures.

INSTRUCTIONS IMPORTANTES :

1. IDENTIFICATION DES DOCUMENTS :
   - Identifie le type de chaque document (Bon de commande, Bon de livraison, Facture, Devis, etc.)
   - Repère le NUMÉRO DE COMMANDE ou NUMÉRO DE DOSSIER de chaque document
   - Repère le NOM DU FOURNISSEUR de chaque document
   - Note la date de chaque document

2. REGROUPEMENT PAR COMMANDE :
   - Regroupe les documents qui concernent la MÊME COMMANDE en utilisant :
     * Le numéro de commande ou numéro de dossier
     * ET le même fournisseur
   - Exemple : BC-1234 (Fournisseur A) + BL-5678 (Fournisseur A) + Facture-999 (Fournisseur A) = MÊME COMMANDE

3. EXTRACTION DES DONNÉES :
   Pour chaque article/produit mentionné, extrais :
   - Numéro de ligne dans le document (ligne 1, ligne 2, etc.)
   - Désignation exacte du produit
   - Quantité commandée (si présente dans bon de commande)
   - Quantité livrée (si présente dans bon de livraison)
   - Prix unitaire HT
   - Prix total HT
   - TVA applicable

   RÈGLE ABSOLUE POUR LES QUANTITÉS LIVRÉES :
   - Cherche UNIQUEMENT la colonne nommée "Livré" ou "Quantité livrée" ou "Qté livrée"
   - IGNORE COMPLÈTEMENT les colonnes suivantes :
     * "Reliquat" (ce qui MANQUE, pas ce qui est livré)
     * "Reste à livrer"
     * "En attente"
     * "À livrer"
     * "Différence"
   - Seule la colonne "Livré" fait foi pour les quantités RÉELLEMENT REÇUES

4. VÉRIFICATIONS CRITIQUES À EFFECTUER :

   A) VÉRIFICATION DES QUANTITÉS (PRIORITAIRE) :
      Pour chaque article d'une même commande, compare :
      - Quantité commandée VS Quantité livrée (colonne "Livré" uniquement)
      
      RÈGLES D'ERREURS :
      - Si quantité livrée < quantité commandée → ERREUR "Livraison partielle"
      - Si quantité livrée > quantité commandée → ERREUR "Sur-livraison"
      - Si article commandé mais totalement absent de la livraison → ERREUR "Article non livré"
      - Si quantité livrée = quantité commandée → OK
   
   B) VÉRIFICATION DES PRIX :
      - Prix unitaires doivent être identiques entre commande et livraison
      - Prix totaux doivent correspondre à : quantité × prix unitaire
      - Pas d'écart de prix injustifié entre les documents

5. SYNTHÈSE FINALE STRUCTURÉE (champ "details") :
   Rédige un rapport CLAIR et STRUCTURÉ en langage simple :

   A) D'abord, un résumé global :
      "Sur [X] documents analysés : [Y] commandes distinctes identifiées."
      "[Z] commandes sans anomalie, [W] commandes avec anomalies."

   B) Ensuite, pour CHAQUE COMMANDE, un paragraphe structuré :
      
      "📦 COMMANDE N°[XXX] - Fournisseur [Nom] :
      Documents analysés : [Liste des docs avec leurs numéros]
      
      ✓ PRIX : 
      - Montant commandé : [XXX]€ HT
      - Montant facturé : [XXX]€ HT
      - Résultat : [OK / Écart de XXX€]
      
      ⚠️ QUANTITÉS :
      - [Nombre] articles commandés
      - [Nombre] articles reçus
      - Anomalies : [Description simple, ex: "78 pantalons commandés mais seulement 56 reçus (Réf: BL-1234, ligne 3)"]
      
      ────────────────────"

   C) Utilise un langage SIMPLE :
      - Évite le jargon technique
      - Utilise des phrases courtes et claires
      - Structure avec tirets, sauts de ligne, séparateurs visuels
      - Indique toujours les références (numéro de document + ligne)

6. RAPPORT COMPLET OBLIGATOIRE :
   Même en cas d'erreurs, tu DOIS indiquer dans le champ "verification_positive" ce qui est correct.
   Exemple : "Tous les prix unitaires et montants totaux sont corrects et cohérents"

7. FORMAT DE RÉPONSE :
   Réponds UNIQUEMENT avec un objet JSON (sans markdown, sans backticks) :

{
  "status": "success" ou "error",
  "commandes_analysees": 3,
  "commandes_ok": 2,
  "commandes_erreurs": 1,
  "errors": [
    {
      "type": "quantité" ou "prix",
      "severity": "critique" ou "warning",
      "commande_numero": "BC-1234",
      "fournisseur": "Nom du fournisseur",
      "ligne_document1": 3,
      "ligne_document2": 5,
      "description": "Description précise de l'anomalie détectée",
      "article": "Nom exact du produit concerné",
      "quantite_commandee": 10,
      "quantite_livree": 7,
      "ecart": -3,
      "document1": "Type et numéro du document 1 (ex: Bon de commande N°123)",
      "document2": "Type et numéro du document 2 (ex: Bon de livraison N°456)"
    }
  ],
  "verification_positive": "Liste des points qui sont corrects (prix, TVA, etc.)",
  "details": "Rapport structuré complet comme décrit ci-dessus"
}

RÈGLES ABSOLUES : 
1. Regroupe TOUJOURS les documents par numéro de commande/dossier ET fournisseur
2. Pour les quantités livrées, utilise UNIQUEMENT la colonne "Livré", JAMAIS le reliquat
3. Toute différence de quantité DOIT être signalée dans "errors"
4. Indique TOUJOURS les numéros de ligne exacts
5. Rédige le champ "details" de manière structurée, claire et facile à lire
6. Remplis TOUJOURS "verification_positive" même en cas d'erreurs

Ne mets RIEN d'autre que le JSON dans ta réponse."""
        })
        
        # Appel à l'API Claude
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": content
            }]
        )
        
        # Extraire et parser la réponse
        response_text = message.content[0].text
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        
        return result
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse : {str(e)}")
        return None

# ============================================
# INTERFACE PRINCIPALE
# ============================================

# HEADER - Titre "Dokii" centré avec accent moderne
st.markdown('''
<div style="text-align: center; margin-bottom: 0.5rem;">
    <h1 class="dokii-title">Dokii</h1>
    <p style="color: #667eea; font-size: 0.9rem; font-weight: 500; letter-spacing: 3px; text-transform: uppercase; margin-top: -0.5rem;">Vérification Intelligente</p>
</div>
''', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# BARRE DE CONFIANCE - Les 4 badges
trust_badges = [
    ("🔒", "TLS", "Sécurisé"),
    ("🛡️", "RGPD", "Conforme"),
    ("🗑️", "Delete", "Suppression auto"),
    ("👁️", "Privé", "Confidentiel")
]

cols = st.columns(4)
for col, (icon, title, subtitle) in zip(cols, trust_badges):
    with col:
        st.markdown(f"""
        <div class="trust-badge">
            <div class="trust-icon">{icon}</div>
            <div class="trust-title">{title}</div>
            <div class="trust-subtitle">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ============================================
# BLOC 1 : CONSENTEMENT
# ============================================
st.markdown('<div class="block-container">', unsafe_allow_html=True)
st.markdown('<h2 class="block-title">🔐 1. Confidentialité</h2>', unsafe_allow_html=True)

st.markdown("""
<p style='font-size: 1rem; line-height: 1.7; color: #CCCCCC;'>
Vos documents sont <strong>chiffrés de bout en bout</strong> (TLS 1.3) et ne sont <strong>jamais stockés</strong> sur nos serveurs. 
L'analyse est effectuée en temps réel puis les données sont <strong>automatiquement supprimées</strong>.<br><br>
Nous sommes <strong>conformes RGPD</strong> et respectons votre vie privée.
</p>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Checkbox de consentement
consent_checkbox = st.checkbox(
    "✓ Je confirme que je ne télécharge pas de données sensibles interdites et j'accepte les CGU.",
    key="consent"
)

st.session_state.consented = consent_checkbox
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# BLOC 2 : UPLOAD (visible seulement si consentement)
# ============================================
if st.session_state.consented:
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="block-title">📂 2. Importez vos documents</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <p style='font-size: 0.95rem; color: #CCCCCC; margin-bottom: 1.5rem;'>
    Téléchargez vos fichiers PDF (bons de commande, bons de livraison, factures, devis, etc.)<br>
    <strong>Aucune limite</strong> sur le nombre de documents.
    </p>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Choisissez vos fichiers",
        type=['pdf'],
        accept_multiple_files=True,
        help="Formats acceptés : PDF uniquement. Aucune limite de nombre.",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # Afficher les fichiers sélectionnés
        st.markdown(f"**{len(uploaded_files)} fichier(s) sélectionné(s) :**")
        for i, file in enumerate(uploaded_files, 1):
            st.markdown(f"📄 {i}. {file.name}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton d'analyse
        if st.button("⚡ Lancer l'analyse", use_container_width=True):
            with st.spinner("🔄 Analyse en cours..."):
                result = analyze_documents(uploaded_files)
                
                if result:
                    st.session_state.analysis_result = result
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# BLOC 3 : RÉSULTATS (visible après analyse)
# ============================================
if st.session_state.consented and st.session_state.analysis_result:
    result = st.session_state.analysis_result
    
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="block-title">📊 3. Rapport d\'analyse</h2>', unsafe_allow_html=True)
    
    # Résumé global en haut
    if result.get('commandes_analysees'):
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1a1a1a 0%, #222222 100%); border: 1px solid #667eea; border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);'>
            <strong style='color: #667eea; font-size: 1.1rem;'>📊 Résumé global</strong><br>
            <span style='font-size: 0.95rem; color: #FFFFFF; margin-top: 0.5rem; display: block;'>
            {result.get('commandes_analysees', 0)} commande(s) analysée(s) •
            {result.get('commandes_ok', 0)} sans anomalie •
            {result.get('commandes_erreurs', 0)} avec anomalies
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    if result['status'] == 'success':
        st.success("✅ **Aucune anomalie détectée**")
        
        # Afficher les vérifications positives
        if result.get('verification_positive'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"✓ **Points validés :** {result['verification_positive']}")
    else:
        st.error(f"⚠️ **{len(result['errors'])} anomalie(s) détectée(s)**")
        
        # Afficher d'abord ce qui est correct
        if result.get('verification_positive'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);'>
                <strong style='color: #FFFFFF; font-size: 1.1rem;'>✓ Points validés</strong><br>
                <span style='font-size: 0.95rem; color: #FFFFFF; margin-top: 0.5rem; display: block;'>
                {result['verification_positive']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tableau des anomalies avec numéros de ligne
        for i, error in enumerate(result['errors'], 1):
            severity_icon = "🔴" if error.get('severity') == 'critique' else "🟠"
            
            with st.expander(f"{severity_icon} Anomalie #{i} - {error.get('type', 'Erreur').capitalize()}", expanded=True):
                # Informations sur la commande
                if error.get('commande_numero'):
                    st.markdown(f"**📦 Commande :** {error.get('commande_numero')}")
                if error.get('fournisseur'):
                    st.markdown(f"**🏢 Fournisseur :** {error.get('fournisseur')}")
                
                st.markdown("---")
                
                # Informations sur les lignes
                ligne_info = ""
                if error.get('ligne_document1'):
                    ligne_info += f"📍 **Ligne {error.get('ligne_document1')}** dans {error.get('document1', 'Document 1')}\n\n"
                if error.get('ligne_document2'):
                    ligne_info += f"📍 **Ligne {error.get('ligne_document2')}** dans {error.get('document2', 'Document 2')}\n\n"
                
                st.markdown(ligne_info)
                
                st.markdown(f"**📦 Article concerné :** {error.get('article', 'N/A')}")
                st.markdown(f"**📝 Description :** {error.get('description', 'N/A')}")
                
                st.markdown("---")
                
                # Quantités si disponibles
                if error.get('quantite_commandee') is not None:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Commandée", error.get('quantite_commandee', 'N/A'))
                    with col2:
                        st.metric("Livrée", error.get('quantite_livree', 'N/A'))
                    with col3:
                        ecart = error.get('ecart', 'N/A')
                        st.metric("Écart", ecart, delta=None if ecart == 'N/A' else f"{ecart}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Rapport détaillé structuré
    if result.get('details'):
        st.markdown("---")
        st.markdown("### 📋 Rapport détaillé")
        st.markdown(f"""
        <div style='background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; white-space: pre-line; line-height: 1.8; color: #FFFFFF;'>
        {result['details']}
        </div>
        """, unsafe_allow_html=True)
    
    # Message de suppression automatique
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%); border-radius: 12px; padding: 1.25rem; margin-top: 1.5rem; box-shadow: 0 4px 20px rgba(168, 85, 247, 0.3);'>
        <strong style='color: #FFFFFF; font-size: 1.1rem;'>🗑️ Données supprimées</strong><br>
        <span style='font-size: 0.9rem; color: #FFFFFF; margin-top: 0.5rem; display: block;'>
        Vos documents ont été automatiquement supprimés de nos serveurs après l'analyse.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bouton pour nouvelle analyse
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Nouvelle analyse", use_container_width=True):
        st.session_state.analysis_result = None
        st.rerun()

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666666; font-size: 0.85rem;'>
    <p>Dokii - Vérification intelligente de documents • Conforme RGPD • Made with ❤️</p>
</div>
""", unsafe_allow_html=True)
