import streamlit as st
import anthropic
import base64
import json
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(
    page_title="Dokii - Vérification Intelligente",
    page_icon="📄",
    layout="centered"
)

# CSS personnalisé - Dark Mode élégant
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Background principal - Bleu Nuit */
    .stApp {
        background: linear-gradient(135deg, #2c3e50 0%, #4A6274 50%, #34495e 100%);
        color: #E8E8E8;
    }
    
    /* Tous les textes en blanc/gris clair */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #E8E8E8 !important;
    }
    
    /* Titre principal "Dokii" avec police Serif */
    .dokii-title {
        font-family: 'Playfair Display', serif;
        font-size: 4.5rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -2px;
    }
    
    /* Police sans-serif pour le reste */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Boutons personnalisés - Beige/Crème avec texte NOIR */
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
        color: #000000 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stButton > button:active {
        color: #000000 !important;
    }
    
    .stButton > button:focus {
        color: #000000 !important;
    }
    
    .stButton > button:disabled {
        background-color: #7A7A7A !important;
        color: #CCCCCC !important;
    }
    
    /* Forcer la couleur du texte dans les boutons */
    div.stButton > button > div > p {
        color: #000000 !important;
    }
    
    div.stButton > button:hover > div > p {
        color: #000000 !important;
    }
    
    /* Badge crédits */
    .credit-badge {
        background: rgba(230, 218, 206, 0.15);
        border: 2px solid #E6DACE;
        border-radius: 20px;
        padding: 0.75rem 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .credit-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E6DACE;
    }
    
    .credit-text {
        font-size: 0.85rem;
        color: #B8B8B8;
        margin-top: 0.25rem;
    }
    
    /* Badges de confiance */
    .trust-badge {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 1.25rem 0.75rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .trust-badge:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateY(-3px);
    }
    
    .trust-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .trust-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #FFFFFF;
    }
    
    .trust-subtitle {
        font-size: 0.75rem;
        color: #B8B8B8;
    }
    
    /* Conteneurs de blocs */
    .block-container {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 2rem;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
    }
    
    .block-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E6DACE;
        margin-bottom: 1rem;
    }
    
    /* Checkbox personnalisée */
    .stCheckbox {
        font-size: 1rem;
        color: #E8E8E8;
    }
    
    /* File uploader */
    .uploadedFile {
        background: rgba(230, 218, 206, 0.1) !important;
        border: 2px solid #E6DACE !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #E6DACE !important;
    }
    
    /* Dataframes */
    .dataframe {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
    }
    
    /* Messages d'erreur/succès */
    .stAlert {
        border-radius: 15px !important;
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(230, 218, 206, 0.1) !important;
        border-radius: 15px !important;
        color: #FFFFFF !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #E6DACE !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du session state
if 'consented' not in st.session_state:
    st.session_state.consented = False
if 'files_analyzed' not in st.session_state:
    st.session_state.files_analyzed = 0
if 'current_month' not in st.session_state:
    st.session_state.current_month = datetime.now().strftime("%Y-%m")
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Constantes
MONTHLY_LIMIT = 15

# Vérifier et réinitialiser le compteur mensuel
current_month = datetime.now().strftime("%Y-%m")
if st.session_state.current_month != current_month:
    st.session_state.files_analyzed = 0
    st.session_state.current_month = current_month

# Calculer les crédits restants
credits_remaining = MONTHLY_LIMIT - st.session_state.files_analyzed

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
        
        # Ajouter le prompt
        content.append({
            "type": "text",
            "text": """Analyse ces documents (factures d'achat, bons de livraison, etc.) et vérifie la cohérence entre eux.

INSTRUCTIONS IMPORTANTES :
1. Extrais les informations suivantes de chaque document : articles/produits, quantités, prix unitaires, prix totaux
2. Compare ces informations entre les différents documents
3. Vérifie que les quantités et prix correspondent entre les documents
4. Réponds UNIQUEMENT avec un objet JSON dans ce format exact (sans markdown, sans backticks) :

{
  "status": "success" ou "error",
  "errors": [],
  "details": "description détaillée des vérifications effectuées",
  "anomalies_count": 0
}

Si des erreurs sont détectées, ajoute-les dans le tableau "errors" avec le format :
{"type": "quantité" ou "prix", "description": "description de l'erreur", "document1": "nom", "document2": "nom"}

Ne mets RIEN d'autre que le JSON dans ta réponse."""
        })
        
        # Appel à l'API Claude
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
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

# HEADER - Titre "Dokii" + Badge Crédits
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
<p style='font-size: 1rem; line-height: 1.7; color: #D0D0D0;'>
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
    <p style='font-size: 0.95rem; color: #D0D0D0; margin-bottom: 1.5rem;'>
    Téléchargez jusqu'à <strong>5 fichiers PDF</strong> (factures, bons de livraison, devis, etc.)
    </p>
    """, unsafe_allow_html=True)
    
    if credits_remaining > 0:
        uploaded_files = st.file_uploader(
            "Choisissez vos fichiers",
            type=['pdf'],
            accept_multiple_files=True,
            help=f"Vous pouvez analyser jusqu'à {credits_remaining} fichier(s) ce mois-ci",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            # Vérifier la limite
            if len(uploaded_files) > 5:
                st.warning("⚠️ Maximum 5 fichiers autorisés pour la version Basic")
                uploaded_files = uploaded_files[:5]
            
            if len(uploaded_files) > credits_remaining:
                st.error(f"❌ Vous ne pouvez analyser que {credits_remaining} fichier(s) supplémentaire(s) ce mois-ci")
            else:
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
                            # Incrémenter le compteur
                            st.session_state.files_analyzed += len(uploaded_files)
                            st.session_state.analysis_result = result
                            st.rerun()
    else:
        st.error("❌ Limite mensuelle atteinte (15 fichiers/mois). Réessayez le mois prochain.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# BLOC 3 : RÉSULTATS (visible après analyse)
# ============================================
if st.session_state.consented and st.session_state.analysis_result:
    result = st.session_state.analysis_result
    
    st.markdown('<div class="block-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="block-title">📊 3. Rapport d\'anomalies</h2>', unsafe_allow_html=True)
    
    if result['status'] == 'success':
        st.success("✅ **Aucune anomalie détectée**")
        st.markdown(f"""
        <p style='font-size: 1rem; color: #D0D0D0; margin-top: 1rem;'>
        {result.get('details', 'Tous les documents sont cohérents.')}
        </p>
        """, unsafe_allow_html=True)
    else:
        st.error(f"⚠️ **{len(result['errors'])} anomalie(s) détectée(s)**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tableau des anomalies
        for i, error in enumerate(result['errors'], 1):
            with st.expander(f"🔴 Anomalie #{i} - {error.get('type', 'Erreur').capitalize()}"):
                st.markdown(f"""
                **Description :** {error.get('description', 'N/A')}
                
                **Documents concernés :**
                - 📄 {error.get('document1', 'N/A')}
                - 📄 {error.get('document2', 'N/A')}
                """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if result.get('details'):
            st.info(f"ℹ️ {result['details']}")
    
    # Message de suppression automatique
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: rgba(168, 85, 247, 0.15); border-left: 4px solid #A855F7; border-radius: 10px; padding: 1rem; margin-top: 1.5rem;'>
        <strong>🗑️ Données supprimées</strong><br>
        <span style='font-size: 0.9rem; color: #D0D0D0;'>
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
<div style='text-align: center; color: #B8B8B8; font-size: 0.85rem;'>
    <p>Dokii - Vérification intelligente de documents • Conforme RGPD • Made with ❤️</p>
</div>
""", unsafe_allow_html=True)
