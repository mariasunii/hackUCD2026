import json
import os
import stripe
from flask import Flask, request
from dotenv import load_dotenv
import db

load_dotenv()
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]

app = Flask(__name__)
db.init_db()


@app.post("/webhook")
def webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")
    try:
        stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)  # verifies signature only
    except Exception:
        return "bad signature", 400

    event = json.loads(payload)  # plain dict, so .get() and ["key"] work

    if db.event_seen(event["id"]):
        return "", 200  # duplicate delivery, already handled

    obj = event["data"]["object"]
    etype = event["type"]

    if etype == "checkout.session.completed":
        if (
            obj.get("mode") == "subscription"
            and obj.get("payment_status") == "paid"
            and obj.get("client_reference_id")
        ):
            db.activate_user(
                obj["client_reference_id"], obj["customer"], obj["subscription"]
            )
            print(f"[webhook] subscription created for user {obj['client_reference_id']}")

    elif etype == "invoice.paid":
        print(f"[webhook] invoice paid: {obj['id']} amount={obj['amount_paid']} {obj['currency']}")

    elif etype == "customer.subscription.updated":
        db.set_status_by_subscription(obj["id"], obj["status"])

    elif etype == "customer.subscription.deleted":
        db.set_status_by_subscription(obj["id"], "canceled")

    return "", 200


if __name__ == "__main__":
    app.run(port=4242)