from fastapi import FastAPI

from database import engine
import models
from routers import users, auth, activities

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(activities.router)

#TODO: Create an activity with location

