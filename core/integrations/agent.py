import os


class AgentPlanner:
    """ADK/Gemini boundary with an explicit local-demo fallback.

    The frontend and workflow engine depend on structured workflow dictionaries,
    never on a particular model response. Production ADK wiring belongs here.
    """

    @property
    def mode(self):
        return "google-adk" if os.getenv("GOOGLE_CLOUD_PROJECT") else "local-simulation"

    def health(self):
        return {
            "mode": self.mode,
            "configured": self.mode == "google-adk",
            "message": "Google Cloud project detected." if self.mode == "google-adk" else "Using deterministic local workflow plans.",
        }

    def propose_workflow(self, organization_description, available_tools):
        raise NotImplementedError(
            "Install and configure google-adk, then implement structured workflow generation at this boundary."
        )
