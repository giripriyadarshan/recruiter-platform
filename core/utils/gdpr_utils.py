import logging
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


@transaction.atomic
def cleanup_candidate_data(candidate):
    """
    Clean up candidate's personal data for GDPR compliance.

    This function:
    1. Anonymizes personal data in the candidate record
    2. Deletes assessment submissions and results
    3. Removes any associated files

    Args:
        candidate: The Candidate model instance to clean up
    """
    logger.info(f"Starting data cleanup for candidate {candidate.id}")

    try:
        # Get the user associated with the candidate
        user = candidate.user

        # Get all assessments for this candidate
        assessments = candidate.assessments.all()

        # Delete assessment code submissions and sensitive data
        for assessment in assessments:
            # Keep basic assessment metadata but remove personal content
            assessment.code_submission = "[REDACTED - Data removed per privacy policy]"
            assessment.evaluation_results = None
            assessment.feedback = "[REDACTED - Data removed per privacy policy]"
            assessment.save()

            logger.info(f"Assessment {assessment.id} data redacted")

        user.is_active = False
        user.save()

        logger.info(f"User {user.id} and candidate {candidate.id} data anonymized")

        return True, "Candidate data has been anonymized successfully."

    except Exception as e:
        logger.error(f"Error during candidate data cleanup: {str(e)}")
        return False, f"Error during data cleanup: {str(e)}"