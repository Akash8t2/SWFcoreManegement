# FallenRobot/modules/sql/chat_context.py

# In-memory store (resets when bot restarts)
user_contexts = {}

def get_context(user_id):
    return user_contexts.get(user_id, "")

def set_context(user_id, context):
    user_contexts[user_id] = context

def clear_context(user_id):
    if user_id in user_contexts:
        del user_contexts[user_id]
