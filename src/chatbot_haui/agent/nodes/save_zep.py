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


def node_save_zep(state: AgentState) -> AgentState:
    thread_id = state.get("thread_id")
    if not thread_id:
        return state
    zep = _get_zep_optional()
    if not zep:
        return state
    try:
        zep.add_exchange(thread_id, state["query"], state.get("answer") or "")
    except Exception:
        pass
    return state
