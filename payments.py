import os
from urllib.parse import urlencode

import stripe
import streamlit as st
from dotenv import load_dotenv

import db

load_dotenv()
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
PRICE_ID = os.environ["STRIPE_PRICE_ID"]
APP_URL = os.environ.get("APP_URL", "http://localhost:8501")


def show_paywall(email):
    db.ensure_user(email)
    st.markdown("### Subscribe to continue")
    st.markdown("**Pro plan: €5.00 / month**")
    st.write("Includes: AI task plan from your assignment brief, shared task board, invite links.")

    return_url = f"{APP_URL}/?{urlencode({'email': email})}"

    if st.button("Subscribe, €5/month", key="subscribe_btn"):
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": PRICE_ID, "quantity": 1}],
                client_reference_id=email,
                customer_email=email,
                success_url=return_url,
                cancel_url=return_url,
            )
            st.link_button("Go to Stripe Checkout", session.url)
        except Exception as exc:
            st.error(f"Could not start checkout. Please try again. ({exc})")

    st.button("I've paid, refresh", key="refresh_btn")