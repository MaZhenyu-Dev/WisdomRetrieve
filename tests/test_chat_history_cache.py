import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, ChatHistory, ChatSession
from app.service.chat_service import _question_hash, _refresh_repeated_cache_hit_history


class CacheHitHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        self.session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def test_refreshes_consecutive_repeated_cache_hit_history(self) -> None:
        old_time = datetime(2024, 1, 1, 12, 0, 0)
        with self.session_factory() as db:
            db.add(
                ChatSession(
                    id=1,
                    session_id="demo",
                    title="hello",
                    created_at=old_time,
                    updated_at=old_time,
                )
            )
            db.add_all(
                [
                    ChatHistory(
                        id=1,
                        session_id="demo",
                        role="user",
                        content="hello",
                        create_time=old_time,
                    ),
                    ChatHistory(
                        id=2,
                        session_id="demo",
                        role="assistant",
                        content="cached answer",
                        create_time=old_time + timedelta(seconds=1),
                    ),
                ]
            )
            db.commit()

            refreshed = _refresh_repeated_cache_hit_history(db, "demo", _question_hash("hello"))
            db.commit()

            self.assertTrue(refreshed)
            rows = list(db.scalars(select(ChatHistory).order_by(ChatHistory.id.asc())))
            self.assertEqual(len(rows), 2)
            self.assertGreater(rows[0].create_time, old_time)
            self.assertGreater(rows[1].create_time, old_time)
            chat_session = db.scalar(select(ChatSession).where(ChatSession.session_id == "demo"))
            self.assertIsNotNone(chat_session)
            self.assertGreater(chat_session.updated_at, old_time)

    def test_does_not_refresh_different_question_hash(self) -> None:
        old_time = datetime(2024, 1, 1, 12, 0, 0)
        with self.session_factory() as db:
            db.add(
                ChatSession(
                    id=1,
                    session_id="demo",
                    title="hello",
                    created_at=old_time,
                    updated_at=old_time,
                )
            )
            db.add_all(
                [
                    ChatHistory(
                        id=1,
                        session_id="demo",
                        role="user",
                        content="hello",
                        create_time=old_time,
                    ),
                    ChatHistory(
                        id=2,
                        session_id="demo",
                        role="assistant",
                        content="cached answer",
                        create_time=old_time + timedelta(seconds=1),
                    ),
                ]
            )
            db.commit()

            refreshed = _refresh_repeated_cache_hit_history(db, "demo", _question_hash("other"))

            self.assertFalse(refreshed)
            rows = list(db.scalars(select(ChatHistory).order_by(ChatHistory.id.asc())))
            self.assertEqual(rows[0].create_time, old_time)
            self.assertEqual(rows[1].create_time, old_time + timedelta(seconds=1))


if __name__ == "__main__":
    unittest.main()
