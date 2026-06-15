from fastapi import FastAPI, Request, Response, HTTPException, status
import httpx
import redis.asyncio as aioredis

app = FastAPI(title="Billing & Subscription API Gateway")

ROUTING_TABLE = {
    "billing": "http://mock_billing_service:8000"
}

async_client = httpx.AsyncClient()
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = aioredis.from_url("redis://redis-server:6379", decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await async_client.close()
    await redis_client.close()

# ---- LAYER 1: RATE LIMITER (HIZ SINIRLAMA) ----
async def is_rate_limited(client_ip: str) -> bool:
    """
    IP başına dakikada maksimum 5 isteğe izin verir.
    """
    redis_key = f"rate_limit:{client_ip}"
    
    # IP'ye ait sayacı 1 artırıyoruz (Anahtar yoksa otomatik oluşturur)
    current_requests = await redis_client.incr(redis_key)
    
    # Eğer bu IP'nin ilk isteğiyse, anahtara 60 saniyelik ömür (TTL) biçiyoruz
    if current_requests == 1:
        await redis_client.expire(redis_key, 60)
        
    # Belirlenen limiti (5 istek) aştıysa True döner
    if current_requests > 5:
        return True
    return False

# ---- LAYER 2: IDEMPOTENCY CHECK (ÇİFT İSTEK ENGELLEME) ----
async def check_idempotency(request: Request):
    if request.method in ["POST", "PUT", "PATCH"]:
        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return
        
        is_unique = await redis_client.set(
            name=f"idempotency:{idempotency_key}", 
            value="PROCESSING", 
            ex=10, 
            nx=True
        )
        if not is_unique:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate request detected. This billing transaction is already being processed."
            )

# ---- CORE ROUTER ----
@app.api_route("/{service_name}/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(service_name: str, rest_of_path: str, request: Request):
    if service_name not in ROUTING_TABLE:
        raise HTTPException(status_code=404, detail="Service not found on API Gateway")
    
    # 1. KORUMA KATMANI: Rate Limiting (Tüm istek metotları için geçerli)
    client_ip = request.client.host
    if await is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. You can only make 5 requests per minute."
        )
    
    # 2. KORUMA KATMANI: Idempotency (Sadece POST/PUT/PATCH için geçerli)
    await check_idempotency(request)
    
    # 3. ADIM: İsteği Yönlendir
    target_base_url = ROUTING_TABLE[service_name]
    target_url = f"{target_base_url}/{rest_of_path}"
    
    query_params = request.query_params
    headers = dict(request.headers)
    body = await request.body()
    headers.pop("host", None)
    
    try:
        response = await async_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=query_params,
            content=body,
            timeout=10.0
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Target service unreachable: {exc}")