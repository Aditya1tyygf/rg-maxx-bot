from fastapi import FastAPI

app = FastAPI()

@app.get("/")
@app.get("/api/index")
def test():
    return {"message": "Vercel Python is working perfectly!"}
