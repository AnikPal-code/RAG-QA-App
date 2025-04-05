import streamlit as st
import joblib
import pandas as pd

# Load model
model = joblib.load("xgboost_fraud_model.pkl")

# Custom page layout
st.set_page_config(page_title="Fraud Detector", layout="wide")

# Add styling
st.markdown("""
    <style>
    .side-design {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        font-weight: bold;
        color: #444;
    }
    </style>
""", unsafe_allow_html=True)

# Layout: 3 columns — side design | main content | side design
left_col, center_col, right_col = st.columns([1, 2, 1])

with left_col:
    st.markdown('<div class="side-design">🧠 AI Model<br>Smart & Secure</div>', unsafe_allow_html=True)

with center_col:
    st.title("💳 Fraud Transaction Predictor")
    st.markdown("Fill in the transaction details to check if it's fraudulent.")

    step = st.number_input("Step", min_value=1)
    amount = st.number_input("Transaction Amount", min_value=0.0)
    oldbalanceOrig = st.number_input("Old Balance (Origin)", min_value=0.0)
    newbalanceOrig = st.number_input("New Balance (Origin)", min_value=0.0)
    oldbalanceDest = st.number_input("Old Balance (Destination)", min_value=0.0)
    newbalanceDest = st.number_input("New Balance (Destination)", min_value=0.0)

    flagged_option = st.selectbox("Is Flagged Fraud?", ["No", "Yes"])
    isFlaggedFraud = 1 if flagged_option == "Yes" else 0

    txn_type = st.selectbox("Transaction Type", ["CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"])

    balance_change = oldbalanceOrig - newbalanceOrig
    dest_balance_change = newbalanceDest - oldbalanceDest
    transaction_ratio = amount / (oldbalanceDest + 1e-6)

    # Create input DataFrame
    input_data = pd.DataFrame([{
        'step': step,
        'amount': amount,
        'newbalanceOrig': newbalanceOrig,
        'oldbalanceDest': oldbalanceDest,
        'newbalanceDest': newbalanceDest,
        'isFlaggedFraud': isFlaggedFraud,
        'type_CASH_OUT': 1 if txn_type == "CASH_OUT" else 0,
        'type_DEBIT': 1 if txn_type == "DEBIT" else 0,
        'type_PAYMENT': 1 if txn_type == "PAYMENT" else 0,
        'type_TRANSFER': 1 if txn_type == "TRANSFER" else 0,
        'balance_change': balance_change,
        'dest_balance_change': dest_balance_change,
        'transaction_ratio': transaction_ratio
    }])

    if st.button("Predict Fraud"):
        proba = model.predict_proba(input_data)[0][1]
        threshold = 0.5  # Fixed threshold at 0.5
        prediction = 1 if proba >= threshold else 0

        st.write(f"🧮 **Fraud Probability:** `{proba:.2%}`")

        if prediction == 1:
            st.error("⚠️ This transaction is **Fraudulent**!")
        else:
            st.success("✅ This transaction is **Not Fraudulent**.")

with right_col:
    st.markdown('<div class="side-design">🔒 Secure<br>Real-time Check</div>', unsafe_allow_html=True)
