# ********************************************************************
# Name    : Consistency Audit
# Summary : Functionality to create consistency audit jobs.
# ********************************************************************
import time

from enmutils.lib import log
from enmutils.lib.headers import JSON_SECURITY_REQUEST

CREATE_AUDIT_JOB_ENDPOINT = "/cm-audit/v1/jobs"
INVOKE_AUDIT_JOB_ENDPOINT = CREATE_AUDIT_JOB_ENDPOINT + "/{0}/invocations"
POLL_AUDIT_JOB_ENDPOINT = CREATE_AUDIT_JOB_ENDPOINT + "/{0}"


def create_audit_job(user, job_name, node):
    """
    Create a consistency audit jobs with given data

    :type user: `enm_user_2.User`
    :param user: User who will create the job
    :type job_name: str
    :param job_name: job_name for the create audit job
    :type node: str
    :param node: Node name to create the audit job

    :rtype: json dict
    :return: json response
    """
    log.logger.debug("Attempting to create audit job for {0}".format(node))
    payload = {"auditType": "cellConsistency", "scope": node, "name": job_name}
    response = user.post(CREATE_AUDIT_JOB_ENDPOINT, json=payload, headers=JSON_SECURITY_REQUEST)
    response.raise_for_status()
    log.logger.debug("Successfully created audit job with name: {0}".format(job_name))
    return response.json()


def invoke_audit_job(user, create_job_response):
    """
    Function to invoke created audit job

    :type user: `enm_user_2.User`
    :param user: User who will invoke the job
    :type create_job_response: json response
    :param create_job_response: response received from creating audit job
    """
    log.logger.debug("Attempting to invoke audit job {0}".format(create_job_response.get("name")))
    status = create_job_response.get("status")
    name = create_job_response.get("name")
    if status == "CREATED":
        created_job_id = create_job_response.get("id")
        invoke_response = user.post(INVOKE_AUDIT_JOB_ENDPOINT.format(created_job_id), headers=JSON_SECURITY_REQUEST)
        invoke_response.raise_for_status()
        log.logger.debug("Consistency Audit Job {0} invoked successfully".format(name))
    else:
        log.logger.debug("Status returned for creating audit job unexpected. Unable to invoke the job."
                         " Create job name:{0} Status: {1}".format(name, status))


def poll_job_status(user, create_job_response, max_retries, retry_interval):
    """
    Function to poll status of invoked audit job

    :type user: `enm_user_2.User`
    :param user: User who will invoke the job
    :type create_job_response: json response
    :param create_job_response: response received from creating audit job
    :type max_retries: int
    :param max_retries: Maximum retries allowed to poll status of invoked job
    :type retry_interval: int
    :param retry_interval: Interval between each retry
    """
    retry = 1
    name = create_job_response.get("name")
    created_job_id = create_job_response.get("id")
    while retry <= max_retries:
        log.logger.debug("Checking status of invoked audit job in {0} seconds".format(retry_interval))
        time.sleep(retry_interval)
        log.logger.debug("Checking status of invoked audit job {0}. Retry: {1}/{2}".format(name, retry, max_retries))
        response = user.get(POLL_AUDIT_JOB_ENDPOINT.format(created_job_id), headers=JSON_SECURITY_REQUEST)
        response.raise_for_status()
        status = response.json().get("status")
        if status == "CREATED" or status == "EXECUTING":
            log.logger.debug("Job {0} not completed yet, polling status again in {1} "
                             "seconds".format(name, retry_interval))
            retry += 1
        else:
            log.logger.debug("Job {0} completed. Job Status: {1}".format(name, status))
            break

    if retry >= max_retries:
        log.logger.debug("The job {0} took longer than expected to complete. Please check it manually".format(name))
