from app.config.settings import settings

def test_verify_db_name():
    print(f"\n[TEST_DB_NAME] {settings.DATABASE_NAME}\n")
    assert settings.DATABASE_NAME == "intellihire_test"
