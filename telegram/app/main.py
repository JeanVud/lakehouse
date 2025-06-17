from fastapi import FastAPI

app = FastAPI()



@app.get("/")
async def root():
    return {"message": "Hello, World!"}
@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    
    # Path to your Let's Encrypt certificates
    # IMPORTANT: Adjust 'quynhgiang.info' if your domain is different
    CERT_PATH = "/etc/letsencrypt/live/quynhgiang.info"
    FULLCHAIN_PATH = f"{CERT_PATH}/fullchain.pem"
    PRIVKEY_PATH = f"{CERT_PATH}/privkey.pem"

    print(CERT_PATH)
    print('___________')

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,  # Expose on port 443 for HTTPS
        ssl_keyfile=PRIVKEY_PATH,
        ssl_certfile=FULLCHAIN_PATH,
        reload=True # Set to False for production
    )
