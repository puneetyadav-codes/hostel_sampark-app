import os

from integrations import HostelSamparkClient


HOSTEL_SAMPARK_URL = os.environ["HOSTEL_SAMPARK_URL"]
HOSTEL_SAMPARK_API_KEY = os.environ.get("HOSTEL_SAMPARK_API_KEY")

client = HostelSamparkClient(
    HOSTEL_SAMPARK_URL,
    HOSTEL_SAMPARK_API_KEY,
)


def load_grievance_form_options():
    """Use this from the other platform's server to fill its hostel form."""
    return client.get_config()


def submit_hostel_grievance(form_data):
    """Call from a server-side form handler; submits on behalf of verified student."""
    return client.submit_grievance(
        title=form_data["title"],
        description=form_data["description"],
        hostel=form_data["hostel"],
        category=form_data["category"],
        enrollment_no=form_data["enrollment_no"],
    )


def check_hostel_grievance(ticket_id, enrollment_no=None):
    """Check ticket status for reference."""
    return client.get_status(ticket_id, enrollment_no=enrollment_no)
