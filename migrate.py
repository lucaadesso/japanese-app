from app.database import engine, Base
import app.models # to ensure all models are imported
Base.metadata.create_all(bind=engine)
print("Migration completed")
