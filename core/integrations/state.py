import os


class DjangoStateBackend:
    """Marker for the current local Django ORM persistence implementation."""
    name = "django"

    def health(self):
        return {"backend": self.name, "configured": True}


class FirestoreStateBackend:
    """Lazy Firestore connection used only when explicitly configured."""
    name = "firestore"

    def __init__(self):
        # Lazy import keeps local simulation usable without Google packages.
        try:
            from google.cloud import firestore
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-firestore to enable Firestore state.") from exc
        self.client = firestore.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])

    def health(self):
        return {"backend": self.name, "configured": True}


def get_state_backend():
    """Choose persistence from deployment config, defaulting safely to Django."""
    if os.getenv("WORKFLOW_STATE_BACKEND", "django") == "firestore":
        return FirestoreStateBackend()
    return DjangoStateBackend()
