from fastapi import FastAPI, Request, status
from pydantic import BaseModel
import random

app = FastAPI(title="Mock Turkcell Superonline Billing Service")

# İstek gövdesini (Request Body) doğrulamak için Pydantic modeli
class InvoiceRequest(BaseModel) :
    subscription_id: int
    amount: float
    billing_period: str

@app.get("/")
async def root():
    return {"status": "online", "service": "Superonline Billing Service"}

@app.post("/invoice/create", status_code=status.HTTP_201_CREATED)
async def create_invoice(invoice_data: InvoiceRequest, request: Request):
    """
    Gateway'den gelen fatura oluşturma isteklerini karşılayan endpoint.
    """
    # Gateway'in Idempotency Key'i başarıyla ilettiğini doğrulamak için header'ı logluyoruz
    gateway_key = request.headers.get("X-Idempotency-Key", "NOT_PROVIDED")
    
    print(f"[BILLING INFO] Processing invoice for SubID: {invoice_data.subscription_id} | Key: {gateway_key}")
    
    # Gerçek dünyada burada veritabanına kayıt ve banka entegrasyonu olur.
    # Biz sahte bir fatura ID'si (Transaction ID) üretip başarılı dönüyoruz.
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    
    return {
        "success": True,
        "message": "Invoice generated successfully.",
        "transaction_id": transaction_id,
        "subscription_id": invoice_data.subscription_id,
        "amount": invoice_data.amount,
        "period": invoice_data.billing_period,
        "processed_by_key": gateway_key
    }