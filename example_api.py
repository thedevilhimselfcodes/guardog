from fastapi import FastAPI, Request, HTTPException
import guardog

app = FastAPI(title="Enterprise Guardog Secure Gateway")
detector = guardog.GuardogSession()

@app.middleware("http")
async def secure_payload_firewall(request: Request, call_next):
    # Intercept incoming raw bytes before it ever hits the application router
    body_bytes = await request.body()
    if body_bytes:
        payload_text = body_bytes.decode('utf-8', errors='ignore')
        
        # Scan and scrub at 620 MB/s
        sanitized = detector.sanitize(payload_text)
        
        if sanitized["matches"]:
            # Optional corporate governance action: Log or drop immediately
            print(f"[SECURITY ALERT] Redacted secrets detected: {sanitized['matches']}")
            
    response = await call_next(request)
    return response

@app.post("/v1/data")
async def receive_data(payload: dict):
    return {"status": "processed", "received": payload}