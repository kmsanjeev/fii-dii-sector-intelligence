from __future__ import annotations

from engines.ai.chat_history.service import ChatHistoryService


def _session(session_id: str, *, updated_at: int, title: str = "Session") -> dict:
    return {
        "id": session_id,
        "title": title,
        "messages": [
            {
                "role": "user",
                "content": "hello",
                "ts": updated_at,
            }
        ],
        "backendSessionId": "srv-1",
        "createdAt": updated_at - 10,
        "updatedAt": updated_at,
    }


def test_chat_history_service_upserts_and_lists_sessions(tmp_dir):
    service = ChatHistoryService(storage_dir=tmp_dir)

    service.upsert_session("client::alpha", _session("chat-1", updated_at=100, title="Older"))
    service.upsert_session("client::alpha", _session("chat-2", updated_at=200, title="Newer"))

    sessions = service.list_sessions("client::alpha")

    assert [session["id"] for session in sessions] == ["chat-2", "chat-1"]
    assert sessions[0]["title"] == "Newer"


def test_chat_history_service_keeps_owners_isolated(tmp_dir):
    service = ChatHistoryService(storage_dir=tmp_dir)

    service.upsert_session("client::alpha", _session("chat-1", updated_at=100))
    service.upsert_session("client::beta", _session("chat-2", updated_at=200))

    assert [session["id"] for session in service.list_sessions("client::alpha")] == ["chat-1"]
    assert [session["id"] for session in service.list_sessions("client::beta")] == ["chat-2"]


def test_chat_history_service_deletes_single_and_all_sessions(tmp_dir):
    service = ChatHistoryService(storage_dir=tmp_dir)

    service.upsert_session("client::alpha", _session("chat-1", updated_at=100))
    service.upsert_session("client::alpha", _session("chat-2", updated_at=200))

    assert service.delete_session("client::alpha", "chat-1") is True
    assert [session["id"] for session in service.list_sessions("client::alpha")] == ["chat-2"]

    deleted = service.delete_all_sessions("client::alpha")

    assert deleted == 1
    assert service.list_sessions("client::alpha") == []
