import streamlit as st
import anthropic
import base64
import json
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(
    page_title="DocVerify AI - Vérification Intelligente",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé pour un design moderne
st.markdown("""
<style>
    /* Fond général */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
    }
    
    /* Headers */
    h1 {
        color: white !important;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 1rem !important;
        background: linear-gradient(90deg, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    h2, h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Cards modernes */
    .modern-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .white-card {
        background: white;
        border-radius: 1.5rem;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    }
    
    /* Boutons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #10b981) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 1rem !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 30px rgba(37, 99, 235, 0.6) !important;
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #64748b, #94a3b8) !important;
        cursor: not-allowed !important;
    }
    
    /* File uploader */
    .uploadedFile {
        background: linear-gradient(135deg, #f8fafc, #e0f2fe) !important;
        border-radius: 1rem !important;
        border: 2px solid #3b82f6 !important;
        padding: 1rem !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #2563eb, #10b981) !important;
        border-radius: 1rem !important;
    }
    
    /* Success/Error boxes */
    .success-box {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        border-left: 5px solid #10b981;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        border-left: 5px solid #ef4444;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    
    .badge-free {
        background: linear-gradient(135deg, #60a5fa, #34d399);
        color: white;
    }
    
    .badge-secure {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid #10b981;
    }
    
    /* Text colors */
    .text-white {
        color: white !important;
    }
    
    .text-slate {
        color: #cbd5e1 !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 1rem !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    /* Info/Warning messages */
    .stAlert {
        border-radius: 1rem !important;
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

# Constantes
MONTHLY_LIMIT = 15

# Vérifier et réinitialiser le compteur mensuel
current_month = datetime.now().strftime("%Y-%m")
if st.session_state.current_month != current_month:
    st.session_state.files_analyzed = 0
    st.session_state.current_month = current_month

# Fonction pour encoder un fichier en base64
def encode_file_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

# Fonction pour analyser les documents avec Claude
def analyze_documents(files):
    try:
        # Récupérer la clé API depuis les secrets ou variables d'environnement
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
        
        if not api_key:
            st.error("⚠️ Clé API Anthropic non configurée. Veuillez ajouter ANTHROPIC_API_KEY dans les secrets.")
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
  "details": "description détaillée des vérifications effectuées"
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

# Interface principale
def main():
    remaining_files = MONTHLY_LIMIT - st.session_state.files_analyzed
    percentage_used = (st.session_state.files_analyzed / MONTHLY_LIMIT) * 100
    
    # Page d'accueil avec consentement
    if not st.session_state.consented:
        # Header avec logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h1>🛡️ DocVerify AI</h1>", unsafe_allow_html=True)
            st.markdown("<p class='text-slate' style='text-align: center; font-size: 1.2rem;'>Vérification Intelligente de Documents</p>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Badge version gratuite
        st.markdown("""
        <div style='text-align: center; margin: 2rem 0;'>
            <span class='badge badge-free'>⚡ VERSION GRATUITE • 15 fichiers/mois</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Compteur d'utilisation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div class='modern-card'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>📊 Utilisation mensuelle</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 2rem; color: {'#ef4444' if remaining_files == 0 else '#60a5fa'}; font-weight: bold;'>{st.session_state.files_analyzed} / {MONTHLY_LIMIT}</p>", unsafe_allow_html=True)
            st.progress(percentage_used / 100)
            if remaining_files > 0:
                st.success(f"✅ {remaining_files} analyse{'s' if remaining_files > 1 else ''} disponible{'s' if remaining_files > 1 else ''}")
            else:
                st.error("⚠️ Limite atteinte • Renouvellement le 1er du mois")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Features
        col1, col2, col3, col4 = st.columns(4)
        features = [
            ("🔒", "Chiffré", "TLS 1.3"),
            ("🛡️", "RGPD", "Conforme UE"),
            ("🗑️", "Éphémère", "Auto-delete"),
            ("👁️", "Privé", "100%")
        ]
        
        for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
            with col:
                st.markdown(f"""
                <div class='modern-card' style='text-align: center; padding: 1.5rem;'>
                    <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>{icon}</div>
                    <div style='color: white; font-weight: bold; font-size: 1.1rem;'>{title}</div>
                    <div style='color: #cbd5e1; font-size: 0.85rem;'>{desc}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Carte de sécurité
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown("<div class='white-card'>", unsafe_allow_html=True)
            st.markdown("<h2 style='color: #1e293b !important;'>🔐 Sécurité & Confidentialité</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>Protection maximale de vos données sensibles</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Features détaillées
            features_detail = [
                ("🔒", "Chiffrement total", "Protocole TLS 1.3 pour une protection maximale"),
                ("💾", "Zéro stockage", "Aucune sauvegarde permanente, traitement en temps réel"),
                ("🛡️", "Conformité RGPD", "Respect total des normes européennes"),
                ("🗑️", "Suppression auto", "Effacement immédiat après analyse")
            ]
            
            for icon, title, desc in features_detail:
                st.markdown(f"""
                <div style='display: flex; align-items: start; margin: 1.5rem 0;'>
                    <div style='font-size: 2rem; margin-right: 1rem;'>{icon}</div>
                    <div>
                        <div style='color: #1e293b; font-weight: bold; font-size: 1.1rem;'>{title}</div>
                        <div style='color: #64748b;'>{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Consentement
            st.markdown("""
            <div style='background: linear-gradient(135deg, #dbeafe, #d1fae5); border: 2px solid #3b82f6; border-radius: 1rem; padding: 1.5rem;'>
                <p style='color: #1e293b; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;'>
                    ✓ J'accepte le traitement sécurisé de mes documents
                </p>
                <p style='color: #475569; font-size: 0.95rem;'>
                    Traitement confidentiel conforme RGPD avec suppression automatique après analyse
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bouton de consentement
            if remaining_files > 0:
                if st.button("🚀 Commencer l'analyse", key="consent_btn", use_container_width=True):
                    st.session_state.consented = True
                    st.rerun()
            else:
                st.button("⚠️ Limite mensuelle atteinte", disabled=True, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Footer
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
                <span class='badge' style='background: rgba(16, 185, 129, 0.2); color: #10b981;'>✓ RGPD Certifié</span>
                <span class='badge' style='background: rgba(59, 130, 246, 0.2); color: #3b82f6;'>🔒 SSL/TLS 1.3</span>
                <span class='badge' style='background: rgba(168, 85, 247, 0.2); color: #a855f7;'>🌍 Hébergement EU</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Interface principale après consentement
    else:
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("<h1 style='text-align: left; font-size: 2.5rem;'>🛡️ DocVerify AI</h1>", unsafe_allow_html=True)
            st.markdown("<p class='text-slate' style='font-size: 1rem;'>Vérification intelligente de documents</p>", unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style='text-align: right; margin-top: 1rem;'>
                <span class='badge badge-free'>Version Gratuite</span>
                <span class='badge badge-secure'>🔒 Sécurisé</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Compteur d'utilisation
        st.markdown("<div class='white-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("<h3 style='color: #1e293b !important;'>📊 Utilisation mensuelle</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #64748b; font-size: 0.9rem;'>Renouvellement automatique chaque mois</p>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<p style='text-align: right; font-size: 3rem; color: {'#ef4444' if remaining_files == 0 else '#3b82f6'}; font-weight: 900; line-height: 1;'>{st.session_state.files_analyzed}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; color: #64748b; font-size: 0.9rem;'>sur {MONTHLY_LIMIT}</p>", unsafe_allow_html=True)
        
        st.progress(percentage_used / 100)
        
        if remaining_files > 0:
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between; margin-top: 1rem;'>
                <span style='color: #10b981; font-weight: 600;'>✓ {remaining_files} analyse{'s' if remaining_files > 1 else ''} disponible{'s' if remaining_files > 1 else ''}</span>
                <span style='color: #64748b; font-size: 0.9rem;'>{int(percentage_used)}% utilisé</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("⚠️ Limite atteinte • Renouvellement le 1er du mois")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Upload de fichiers
        if remaining_files > 0:
            st.markdown("<div class='white-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #1e293b !important;'>📁 Téléchargez vos documents</h3>", unsafe_allow_html=True)
            
            uploaded_files = st.file_uploader(
                "Déposez vos fichiers PDF ici",
                type=['pdf'],
                accept_multiple_files=True,
                help="Formats acceptés : PDF uniquement"
            )
            
            if uploaded_files:
                st.success(f"✅ {len(uploaded_files)} fichier{'s' if len(uploaded_files) > 1 else ''} sélectionné{'s' if len(uploaded_files) > 1 else ''}")
                
                # Afficher les fichiers
                for file in uploaded_files:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #f8fafc, #e0f2fe); border: 2px solid #3b82f6; border-radius: 1rem; padding: 1rem; margin: 0.5rem 0; display: flex; align-items: center;'>
                        <span style='font-size: 1.5rem; margin-right: 1rem;'>📄</span>
                        <span style='color: #1e293b; font-weight: 600;'>{file.name}</span>
                        <span style='margin-left: auto; color: #10b981;'>🔒</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bouton d'analyse
            if uploaded_files and len(uploaded_files) > 0:
                if st.button("⚡ Lancer l'analyse IA", key="analyze_btn", use_container_width=True):
                    if len(uploaded_files) > remaining_files:
                        st.error(f"❌ Vous ne pouvez analyser que {remaining_files} fichier{'s' if remaining_files > 1 else ''} supplémentaire{'s' if remaining_files > 1 else ''} ce mois-ci")
                    else:
                        with st.spinner("🔄 Analyse en cours..."):
                            result = analyze_documents(uploaded_files)
                            
                            if result:
                                # Incrémenter le compteur
                                st.session_state.files_analyzed += len(uploaded_files)
                                
                                st.markdown("<br>", unsafe_allow_html=True)
                                
                                # Afficher les résultats
                                if result['status'] == 'success':
                                    st.markdown("""
                                    <div class='success-box'>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 4rem; margin-bottom: 1rem;'>✅</div>
                                            <h2 style='color: #10b981 !important; font-size: 2.5rem;'>Aucun problème détecté</h2>
                                            <p style='color: #064e3b; font-size: 1.1rem; margin-top: 1rem;'>{}</p>
                                        </div>
                                    </div>
                                    """.format(result['details']), unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div class='error-box'>
                                        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
                                            <div style='font-size: 3rem; margin-right: 1rem;'>❌</div>
                                            <div>
                                                <h2 style='color: #ef4444 !important; margin: 0;'>Erreurs détectées</h2>
                                                <p style='color: #7f1d1d; margin: 0;'>{len(result['errors'])} incohérence{'s' if len(result['errors']) > 1 else ''} trouvée{'s' if len(result['errors']) > 1 else ''}</p>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Afficher chaque erreur
                                    for i, err in enumerate(result['errors'], 1):
                                        st.markdown(f"""
                                        <div class='error-box' style='margin-top: 1rem;'>
                                            <div style='font-weight: bold; color: #991b1b; font-size: 1.1rem; margin-bottom: 0.5rem;'>
                                                Erreur #{i} - Type: {err.get('type', 'N/A')}
                                            </div>
                                            <p style='color: #7f1d1d; font-size: 1rem;'>{err.get('description', 'N/A')}</p>
                                            {f"<p style='color: #991b1b; font-size: 0.9rem; margin-top: 0.5rem;'>📄 Documents: {err.get('document1', '')} ↔ {err.get('document2', '')}</p>" if err.get('document1') or err.get('document2') else ''}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if result.get('details'):
                                        st.info(f"ℹ️ {result['details']}")
                                
                                # Message de suppression
                                st.markdown("""
                                <div style='background: linear-gradient(135deg, #f3e8ff, #e9d5ff); border-left: 5px solid #a855f7; border-radius: 1rem; padding: 1.5rem; margin-top: 1rem;'>
                                    <div style='display: flex; align-items: center;'>
                                        <span style='font-size: 1.5rem; margin-right: 1rem;'>🗑️</span>
                                        <div>
                                            <div style='color: #581c87; font-weight: bold;'>Données supprimées</div>
                                            <div style='color: #6b21a8; font-size: 0.9rem;'>Vos documents ont été automatiquement supprimés après analyse</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Footer
        col1, col2, col3 = st.columns(3)
        with col2:
            st.markdown("""
            <div style='text-align: center;'>
                <span class='badge' style='background: white; color: #10b981; border: 1px solid #10b981;'>🛡️ RGPD</span>
                <span class='badge' style='background: white; color: #3b82f6; border: 1px solid #3b82f6;'>🔒 SSL/TLS</span>
                <span class='badge' style='background: white; color: #a855f7; border: 1px solid #a855f7;'>🌍 EU</span>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
