from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers.products import router as products_router
from app.routers.newsletter import router as newsletter_router
from app.routers.contact import router as contact_router
from app.routers.chat import router as chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://plycraft-frontend.vercel.app", "https://www.plycraft.co.uk"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(products_router)
app.include_router(newsletter_router)
app.include_router(contact_router)
app.include_router(chat_router)

