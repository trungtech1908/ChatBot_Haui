from chatbot_haui.agent.state import AgentState

_zep_memory = None


def _get_zep_optional():
    global _zep_memory
    if _zep_memory is False:
        return None
    if _zep_memory is None:
        try:
            from chatbot_haui.memory.zep import ZepMemory
            _zep_memory = ZepMemory()
        except Exception:
            _zep_memory = False
            return None
    return _zep_memory


def node_zep_context(state: AgentState) -> AgentState:
    user_id = state["user_id"]
    thread_id = state["thread_id"]

    zep = _get_zep_optional()
    if not zep:
        state["zep_context"] = ""
        state["chat_history"] = []
        return state

    try:
        from chatbot_haui.memory.zep import ensure_zep_session
        ensure_zep_session(zep, user_id, thread_id, ho_ten=state.get("ho_ten"))
        state["zep_context"] = zep.get_hybrid_context(
            user_id, thread_id, state.get("query", "")
        )
        state["chat_history"] = zep.get_recent_messages(thread_id)
    except Exception:
        state["zep_context"] = ""
        state["chat_history"] = []
    return state
