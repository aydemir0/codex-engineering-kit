def create_payment(request, database, provider):
    payload = request.json()
    payment = database.insert_payment(
        account_id=payload["account_id"],
        amount=payload["amount"],
        currency=payload["currency"],
    )
    charge = provider.charge(
        account_id=payment.account_id,
        amount=payment.amount,
        currency=payment.currency,
    )
    database.attach_provider_reference(payment.id, charge.id)
    database.commit()
    return {"payment_id": payment.id, "provider_reference": charge.id}
