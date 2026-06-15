# =============================================================
# Onglet MongoDB — Statut Replica Set et Explorateur
# =============================================================

import streamlit as st
import pandas as pd
import json as json_mod
from bson import json_util

from backend.db import check_connection, get_db


def render():
    mongo_info = check_connection()

    # --- Replica Set Status ---
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Statut du Replica Set</h4>", unsafe_allow_html=True)

    if mongo_info["connected"]:
        rs_cols = st.columns(len(mongo_info["members"]))
        for i, member in enumerate(mongo_info["members"]):
            with rs_cols[i]:
                state = member["state"]
                if state == "PRIMARY":
                    color, icon = "#10b981", "P"
                elif state == "SECONDARY":
                    color, icon = "#6366f1", "S"
                else:
                    color, icon = "#f59e0b", "A"
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                st.markdown(f"""
                <div style='text-align: center; background: rgba({r},{g},{b},0.08);
                    border: 1px solid {color}33; border-radius: 12px; padding: 16px;'>
                    <div style='font-family: Outfit; font-size: 2rem; font-weight: 800; color: {color};'>{icon}</div>
                    <div style='font-size: 0.8rem; color: #cbd5e1; margin-top: 4px;'>{member['name']}</div>
                    <div style='font-size: 0.75rem; color: {color}; font-weight: 600; text-transform: uppercase; margin-top: 2px;'>{state}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error(f"MongoDB non connecte : {mongo_info['error']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # --- Collections Explorer ---
    if mongo_info["connected"]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-family: Outfit, sans-serif; margin-top: 0;'>Explorateur de Collections</h4>", unsafe_allow_html=True)

        db_ref = get_db()
        collections = sorted(db_ref.list_collection_names())
        selected = st.selectbox("Collection", collections)

        if selected:
            col_ref = db_ref[selected]
            doc_count = col_ref.count_documents({})
            idx_count = len(col_ref.index_information())

            mc1, mc2 = st.columns(2)
            mc1.metric("Documents", f"{doc_count:,}")
            mc2.metric("Index", idx_count)

            docs = list(col_ref.find().limit(20))
            if docs:
                docs_json = json_mod.loads(json_util.dumps(docs))
                st.dataframe(pd.json_normalize(docs_json), use_container_width=True, hide_index=True)
            else:
                st.info("Collection vide.")

            with st.expander("Index de la collection"):
                for name, info in col_ref.index_information().items():
                    keys = ", ".join(f"{k}: {v}" for k, v in info["key"])
                    unique = " (UNIQUE)" if info.get("unique") else ""
                    st.code(f"{name}: {{{keys}}}{unique}", language="text")

        st.markdown("</div>", unsafe_allow_html=True)
