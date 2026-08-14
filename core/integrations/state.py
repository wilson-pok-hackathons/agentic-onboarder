import os


class DjangoStateBackend:
    name = "django"

    def health(self):
        return {"backend": self.name, "configured": True}


class FirestoreStateBackend:
    name = "firestore"

    def __init__(self):
        try:
            from google.cloud import firestore
        except ImportError as exc:
            raise RuntimeError("Install google-cloud-firestore to enable Firestore state.") from exc
        self.client = firestore.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])

    def health(self):
        return {"backend": self.name, "configured": True}


def get_state_backend():
    if os.getenv("WORKFLOW_STATE_BACKEND", "django") == "firestore":
        return FirestoreStateBackend()
    return DjangoStateBackend()
