from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.restaurants import router as restaurant_router
from app.api.ingredients import router as ingredient_router
from app.api.inventory_movements import router as inventory_movement_router
from app.api.recipes import router as recipe_router
from app.api.orders import router as order_router


app = FastAPI(
    title="KitchenOS API",
    description="AI-powered operating system for restaurants.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(restaurant_router)
app.include_router(ingredient_router)
app.include_router(inventory_movement_router)
app.include_router(recipe_router)
app.include_router(order_router)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "KitchenOS API",
        "version": "0.1.0",
    }