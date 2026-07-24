from app.database import SessionLocal
from app.srs import seed_database
db = SessionLocal()
seed_database(db)
db.close()
print("Seeded")
