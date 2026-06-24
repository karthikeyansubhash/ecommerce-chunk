"""UserRepository: in-memory persistence for user records.

Used by: AuthService, PaymentService.
"""


class UserRepository:
    def __init__(self):
        self._users = {}  # user_id -> dict
        self._next_id = 1

    def create(self, email: str, password_hash: str) -> dict:
        user_id = str(self._next_id)
        self._next_id += 1
        user = {"id": user_id, "email": email, "password_hash": password_hash}
        self._users[user_id] = user
        return user

    def update(self, user_id: str, **fields) -> dict:
        if user_id not in self._users:
            raise KeyError(f"No user with id {user_id}")
        self._users[user_id].update(fields)
        return self._users[user_id]

    def delete(self, user_id: str) -> bool:
        return self._users.pop(user_id, None) is not None

    def find_by_id(self, user_id: str) -> dict:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> dict:
        for user in self._users.values():
            if user["email"] == email:
                return user
        return None
