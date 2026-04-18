from sqlalchemy import create_engine


engine = create_engine(
    "postgresql+psycopg2://admin:password123@postgres:5432/warehouse"
)




