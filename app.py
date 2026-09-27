import streamlit as st
import pandas as pd
from google import genai
import json

st.set_page_config(page_title="MaquisAI Ecosystem", layout="wide", page_icon="🍺")

# Initialisation de la Base de Données Centralisée
if 'stock_central' not in st.session_state:
    st.session_state.stock_central = {
        "Bière Ivoire (66cl)": {"prix": 1000, "stock_bouteilles": 120, "icon": "🍺"},
        "Bock / Solibra (66cl)": {"prix": 800, "stock_bouteilles": 96, "icon": "🍻"},
        "Beaufort Lager (50cl)": {"prix": 1000, "stock_bouteilles": 48, "icon": "🍾"},
        "Guinness (33cl)": {"prix": 1200, "stock_bouteilles": 36, "icon": "🍷"},
        "Sucrerie Coca (50cl)": {"prix": 500, "stock_bouteilles": 60, "icon": "🥤"},
        "Fanta Orange (50cl)": {"prix": 500, "stock_bouteilles": 48, "icon": "🧃"}
    }

if 'journal_ventes' not in st.session_state:
    st.session_state.journal_ventes = []

# Navigation Lateral
with st.sidebar:
    st.title("🌐 MaquisAI Network")
    app_mode = st.radio("SELECTIONNER L'APPLICATION :", ["📱 Application Serveur / Client", "🖥️ Application Gérant (Stock Central & IA)"])
    st.markdown("---")
    st.subheader("⚙️ Connexion IA Gemini")
    api_key = st.text_input("Clé API Google Gemini :", type="password")
    st.caption("Obtenez une clé sur https://aistudio.google.com/")
    st.markdown("---")
    st.success("🟢 Base de données synchronisée")

# ------------------------------------------------------------------------------
# 1. APPLICATION SERVEUR / CLIENT
# ------------------------------------------------------------------------------
if app_mode == "📱 Application Serveur / Client":
    st.title("📱 MaquisAI — Terminal de Prise de Commande")
    st.caption("Interface simplifiée pour les serveurs et clients")

    col_gauche, col_droite = st.columns([2, 1])

    with col_gauche:
        st.subheader("🗣️ Commande Vocale / Texte (IA)")
        cmd_naturelle = st.text_input("Saisissez la commande (ex: '2 bières Ivoire et 1 Coca') :")
        
        if st.button("✨ Valider par l'IA"):
            if not api_key:
                st.error("⚠️ Saisissez la clé API Gemini dans la barre latérale.")
            elif cmd_naturelle:
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    Tu es la caisse IA d'un maquis en Côte d'Ivoire.
                    Voici notre stock disponible : {json.dumps(st.session_state.stock_central)}
                    Client/Serveur dit : "{cmd_naturelle}"

                    Analyse la commande et reponds sous forme de résumé court avec :
                    - La liste des boissons et quantités reconnues.
                    - Le montant total calculé.
                    - Si une boisson est en rupture, indique-le clairement.
                    """
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

        st.markdown("---")
        st.subheader("🍺 Carte des Boissons")
        
        panier = {}
        cols = st.columns(3)
        for i, (boisson, details) in enumerate(st.session_state.stock_central.items()):
            with cols[i % 3]:
                st.markdown(f"#### {details['icon']} {boisson}")
                st.write(f"Prix : **{details['prix']} FCFA**")
                st.write(f"En Stock : **{details['stock_bouteilles']} btl**")
                
                if details['stock_bouteilles'] <= 0:
                    st.error("❌ Épuisé")
                else:
                    qte = st.number_input(f"Quantité", min_value=0, max_value=details['stock_bouteilles'], key=f"cmd_{boisson}")
                    if qte > 0:
                        panier[boisson] = qte

    with col_droite:
        st.subheader("🛒 Panier Actuel")
        if not panier:
            st.info("Aucune boisson sélectionnée.")
        else:
            total = 0
            for item, qte in panier.items():
                prix = st.session_state.stock_central[item]['prix']
                st.write(f"• **{qte}x** {item} : **{qte * prix} FCFA**")
                total += qte * prix
            
            st.markdown("---")
            st.markdown(f"### Total : `{total:,} FCFA`".replace(",", " "))
            
            if st.button("🚀 ENVOYER LA COMMANDE AU STOCK CENTRAL", type="primary", use_container_width=True):
                for item, qte in panier.items():
                    st.session_state.stock_central[item]['stock_bouteilles'] -= qte
                
                st.session_state.journal_ventes.append({
                    "articles": panier,
                    "total": total
                })
                st.success("✅ Commande envoyée et stock mis à jour !")
                st.rerun()

# ------------------------------------------------------------------------------
# 2. APPLICATION GÉRANT & STOCK
# ------------------------------------------------------------------------------
else:
    st.title("🖥️ MaquisAI — Cockpit Gérant & Stock Central")
    st.caption("Espace réservé au propriétaire du maquis")

    ca_total = sum([v['total'] for v in st.session_state.journal_ventes])
    nb_cmd = len(st.session_state.journal_ventes)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Chiffre d'Affaires", f"{ca_total:,} FCFA".replace(",", " "))
    col2.metric("📦 Commandes Reçues", f"{nb_cmd}")
    col3.metric("🍺 Bouteilles Vendues", f"{sum([sum(v['articles'].values()) for v in st.session_state.journal_ventes])}")

    st.markdown("---")
    st.subheader("📊 État du Stock Central Synchronisé")
    
    data_stock = []
    for boisson, details in st.session_state.stock_central.items():
        casiers = details['stock_bouteilles'] // 12
        btl_restantes = details['stock_bouteilles'] % 12
        
        status = "🟢 Bon stock"
        if details['stock_bouteilles'] <= 12:
            status = "🔴 Alerte Rupture !"
        elif details['stock_bouteilles'] <= 24:
            status = "🟡 Stock Faible"

        data_stock.append({
            "Boisson": boisson,
            "Stock Bouteilles": details['stock_bouteilles'],
            "Équivalent Casiers": f"{casiers} casier(s) + {btl_restantes} btl",
            "Prix Unitaire": f"{details['prix']} FCFA",
            "État du Stock": status
        })
    
    st.dataframe(pd.DataFrame(data_stock), use_container_width=True)

    st.markdown("---")
    st.subheader("🧠 Copilote Stratégique IA (Rapport & Commande Brasserie)")
    
    if st.button("🚀 Générer l'Analyse d'Approvisionnement IA", type="primary"):
        if not api_key:
            st.error("⚠️ Veuillez renseigner la clé API Gemini dans la barre latérale.")
        else:
            with st.spinner("Analyse des stocks par l'IA Gemini..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""
                    Tu es l'IA Copilote de gestion stratégique pour le propriétaire d'un maquis en Côte d'Ivoire.
                    
                    Données en temps réel reçues de la caisse :
                    - Chiffre d'Affaires total : {ca_total} FCFA
                    - Journal des ventes : {st.session_state.journal_ventes}
                    - État du stock central actuel : {st.session_state.stock_central}

                    Rédige un rapport structuré et direct pour le gérant :
                    1. 📊 **Synthèse Financière et Tendances** (Produits phares).
                    2. 🚚 **Bon de Commande Brasserie** (Nombre précis de casiers de 12 bouteilles à commander pour chaque boisson afin d'éviter les ruptures).
                    3. 💡 **2 Conseils de Gestion** (ex: gestion des casiers vides/consignes, température de refroidissement des bières).
                    """
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )
                    st.success("Analyse terminée !")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Erreur d'analyse : {e}")