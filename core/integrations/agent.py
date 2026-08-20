import os


class AgentPlanner:
    """ADK/Gemini boundary with an explicit local-demo fallback.

    The frontend and workflow engine depend on structured workflow dictionaries,
    never on a particular model response. Production ADK wiring belongs here.
    """

    @property
    def mode(self):
        return os.getenv("AGENT_BACKEND", "local")

    def health(self):
        configured = self.mode == "google-adk"
        return {
            "mode": self.mode,
            "configured": configured,
            "message": (
                "Google ADK mode selected."
                if configured
                else "Using deterministic local workflow plans."
            ),
        }

    def propose_workflow(self, organization_description, available_tools):
        # Fail honestly until ADK is wired instead of returning pretend AI data.
        raise NotImplementedError(
            "Install and configure google-adk, then implement structured workflow generation at this boundary."
        )
