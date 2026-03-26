from fastapi import FastAPI
from api.v1 import users, trades
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Trading Api"
)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://colab.research.google.com",
]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
for route in app.routes:
    print(route.path)
@app.get("/")
async def root():
    return {"message":"Trading Api Running"}
