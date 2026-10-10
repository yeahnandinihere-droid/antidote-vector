import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="AntidoteVector | Toxicokinetic & Dialyzability Engine",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧪 AntidoteVector: Acute Toxicokinetic & Dialyzability Decision Engine")
st.caption("Emergency clinical decision-support evaluating decontamination windows, antidote triggers, and EXTRIP-grade extracorporeal clearance (hemodialysis) criteria.")
st.markdown("---")

# --- Toxicology Drug Knowledge Base ---
DRUG_DATA = {
    "Acetaminophen (APAP)": {
        "mw": 151,
        "vd": 0.9,
        "pb": 20,
        "dialyzable": "Limited / Rarely Indicated",
        "extrip_tier": "Not Routine (Indicated only in massive ingestion with severe mitochondrial acidosis/coma)",
        "antidote": "N-Acetylcysteine (NAC)",
        "has_nomogram": True,
        "decon_window_hrs": 2.0
    },
    "Salicylates (Aspirin)": {
        "mw": 138,
        "vd": 0.2,
        "pb": 50,
        "dialyzable": "Yes (Highly Dialyzable)",
        "extrip_tier": "Level 1A: Strongly Recommended (Level > 90 mg/dL or severe acidosis/altered mental status)",
        "antidote": "IV Sodium Bicarbonate (Urine alkalinization, pH 7.5-8.0)",
        "has_nomogram": False,
        "decon_window_hrs": 2.0
    },
    "Lithium": {
        "mw": 74,
        "vd": 0.7,
        "pb": 0,
        "dialyzable": "Yes (Highly Dialyzable)",
        "extrip_tier": "Level 1A: Strongly Recommended (Chronic > 4.0 mEq/L, or Acute > 5.0 mEq/L, or severe neurotoxicity)",
        "antidote": "None (Hemodialysis is primary modality; IV 0.9% NaCl for rehydration)",
        "has_nomogram": False,
        "decon_window_hrs": 1.0
    },
    "Ethylene Glycol / Methanol (Toxic Alcohols)": {
        "mw": 62,
        "vd": 0.6,
        "pb": 0,
        "dialyzable": "Yes (Highly Dialyzable)",
        "extrip_tier": "Level 1A: Strongly Recommended (Refractory metabolic acidosis, anion gap > 24, or visual impairment)",
        "antidote": "Fomepizole (or Ethanol if unavailable)",
        "has_nomogram": False,
        "decon_window_hrs": 1.0
    },
    "Tricyclic Antidepressants (TCAs - e.g., Amitriptyline)": {
        "mw": 277,
        "vd": 15.0,
        "pb": 95,
        "dialyzable": "No (Futile / Not Dialyzable)",
        "extrip_tier": "Contraindicated / Ineffective (Vd > 10 L/kg; drug resides in tissue, not intravascular space)",
        "antidote": "IV Sodium Bicarbonate (Target arterial pH 7.45-7.55 to overcome fast Na-channel blockade)",
        "has_nomogram": False,
        "decon_window_hrs": 2.0
    },
    "Digoxin": {
        "mw": 781,
        "vd": 7.0,
        "pb": 25,
        "dialyzable": "No (Not Dialyzable)",
        "extrip_tier": "Contraindicated / Ineffective (High Vd; dialyzer removal is negligible)",
        "antidote": "Digoxin Immune Fab (DigiFab)",
        "has_nomogram": False,
        "decon_window_hrs": 1.0
    }
}

# --- Sidebar Inputs ---
st.sidebar.header("🚨 Acute Clinical Presentation")

selected_drug = st.sidebar.selectbox("Suspected Ingestant / Toxin", list(DRUG_DATA.keys()))
drug_info = DRUG_DATA[selected_drug]

time_elapsed = st.sidebar.slider("Time Elapsed Since Ingestion (Hours)", min_value=0.5, max_value=24.0, value=4.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("🧪 Laboratory & Toxin Biomarkers")

if selected_drug == "Acetaminophen (APAP)":
    serum_conc = st.sidebar.number_input("Serum APAP Level (mcg/mL)", min_value=0.0, max_value=800.0, value=180.0, step=5.0)
elif selected_drug == "Salicylates (Aspirin)":
    serum_conc = st.sidebar.number_input("Serum Salicylate Level (mg/dL)", min_value=0.0, max_value=150.0, value=75.0, step=2.0)
elif selected_drug == "Lithium":
    serum_conc = st.sidebar.number_input("Serum Lithium Level (mEq/L)", min_value=0.0, max_value=12.0, value=4.5, step=0.1)
else:
    serum_conc = st.sidebar.number_input("Reported Serum Concentration (arbitrary units)", min_value=0.0, max_value=500.0, value=50.0, step=1.0)

arterial_ph = st.sidebar.number_input("Arterial Blood Gas pH", min_value=6.80, max_value=7.60, value=7.32, step=0.02)
mental_status = st.sidebar.selectbox("Neurological / Clinical Status", ["Alert / Oriented", "Lethargic / Confused", "Stupor / Coma / Seizures"])

# --- 1. Decontamination & Antidote ---
st.subheader("1. ⏳ Decontamination & Immediate Antidote Window")
col_d1, col_d2, col_d3 = st.columns(3)

charcoal_eligible = time_elapsed <= drug_info["decon_window_hrs"] and mental_status != "Stupor / Coma / Seizures"
with col_d1:
    if charcoal_eligible:
        st.success(f"**Activated Charcoal:** Eligible ({time_elapsed}h elapsed ≤ {drug_info['decon_window_hrs']}h window, airway intact).")
    else:
        st.warning(f"**Activated Charcoal:** Not Recommended (Window elapsed or airway/aspiration risk).")

with col_d2:
    st.info(f"**Target Antidote:**\n\n{drug_info['antidote']}")

with col_d3:
    if arterial_ph < 7.20 or mental_status == "Stupor / Coma / Seizures":
        st.error("**Physiologic Alert:** Severe Acidemia / Neuro Compromise detected.")
    else:
        st.success("**Physiologic Status:** Hemodynamically compensable.")

st.markdown("---")

# --- 2. EXTRIP Dialyzability Matrix ---
st.subheader("2. 🏥 Extracorporeal Clearance & EXTRIP Dialyzability Matrix")

col_phys1, col_phys2, col_phys3, col_phys4 = st.columns(4)
col_phys1.metric("Molecular Weight", f"{drug_info['mw']} Da", help="MW < 500 Da filters efficiently across dialyzer membranes")
col_phys2.metric("Volume of Distribution (Vd)", f"{drug_info['vd']} L/kg", help="Vd < 1 L/kg indicates drug remains intravascularly accessible")
col_phys3.metric("Plasma Protein Binding", f"{drug_info['pb']}%", help="Only free unbound drug clears via standard dialysis")
col_phys4.metric("Dialysis Feasibility", drug_info["dialyzable"])

dialysis_indicated = False
if selected_drug == "Salicylates (Aspirin)" and (serum_conc >= 90 or (serum_conc >= 80 and arterial_ph < 7.20) or mental_status == "Stupor / Coma / Seizures"):
    dialysis_indicated = True
elif selected_drug == "Lithium" and (serum_conc >= 4.0 or (serum_conc >= 2.5 and mental_status != "Alert / Oriented")):
    dialysis_indicated = True
elif selected_drug == "Ethylene Glycol / Methanol (Toxic Alcohols)" and (arterial_ph < 7.25 or mental_status == "Stupor / Coma / Seizures"):
    dialysis_indicated = True
elif selected_drug == "Acetaminophen (APAP)" and serum_conc > 500 and arterial_ph < 7.30:
    dialysis_indicated = True

if dialysis_indicated:
    st.error(f"🚨 **EXTRIP CRITERIA MET:** Urgent Hemodialysis Recommended.\n\n*{drug_info['extrip_tier']}*")
else:
    if "No" in drug_info["dialyzable"]:
        st.warning(f"⛔ **HEMODIALYSIS INEFFECTIVE:** {drug_info['extrip_tier']}")
    else:
        st.info(f"ℹ️ **Current Status:** Thresholds for emergent hemodialysis not yet exceeded. Continue medical management and serial monitoring. (*{drug_info['extrip_tier']}*)")

st.markdown("---")

# --- 3. Interactive Nomogram / Targets ---
if selected_drug == "Acetaminophen (APAP)":
    st.subheader("3. 📈 Interactive Rumack-Matthew Nomogram Plot (4–24 Hours)")
    t_nomo = np.linspace(4, 24, 100)
    treatment_line = 150 * (0.5 ** ((t_nomo - 4) / 4))
    high_risk_line = 300 * (0.5 ** ((t_nomo - 4) / 4))

    nomo_df = pd.DataFrame({
        "Hours Post-Ingestion": t_nomo,
        "Treatment Line (150 mcg/mL @ 4h)": np.round(treatment_line, 1),
        "High-Risk Toxicity Line": np.round(high_risk_line, 1)
    }).set_index("Hours Post-Ingestion")

    st.line_chart(nomo_df)

    if time_elapsed >= 4:
        threshold_at_time = 150 * (0.5 ** ((time_elapsed - 4) / 4))
        if serum_conc >= threshold_at_time:
            st.error(f"⚠️ **Above Treatment Line:** Patient level ({serum_conc} mcg/mL at {time_elapsed}h) exceeds the action line ({threshold_at_time:.1f} mcg/mL). Initiate IV N-acetylcysteine immediately.")
        else:
            st.success(f"✅ **Below Treatment Line:** Patient level ({serum_conc} mcg/mL at {time_elapsed}h) is below the action line ({threshold_at_time:.1f} mcg/mL).")
    else:
        st.info("🕒 **Note:** Levels drawn before 4 hours post-ingestion cannot be accurately interpreted on the Rumack-Matthew nomogram. Repeat level at the 4-hour mark.")

elif selected_drug == "Salicylates (Aspirin)":
    st.subheader("3. 📈 Urinary Alkalinization & Clearance Targets")
    st.markdown("""
    * **Urinary Trapping Principle:** Salicylic acid ($pK_a \\approx 3.0$) ionizes at alkaline urine pH, driving renal elimination up by **10- to 20-fold**.
    * **Target Arterial pH:** `7.45 – 7.55` (prevents cerebral penetration by maintaining salicylate in ionized circulating state).
    * **Target Urinary pH:** `7.5 – 8.0` (requires co-administration of IV Sodium Bicarbonate and Potassium repletion).
    """)