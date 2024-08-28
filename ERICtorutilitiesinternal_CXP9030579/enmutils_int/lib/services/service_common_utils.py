# NOTE::
# Module should be used only for common helper functions
# imports to this module from enmutils|enmutils_int should be limited or none at all to reduce circular imports
import commands
import json
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from flask import abort


def get_json_response(success=None, message=None, rc=None, content_type=None):
    """
    Returns a json response with the required response code

    :param success: Boolean indicating if the response to be returned was successful or not
    :type success: bool
    :param message: Message to be returned as part of the response
    :type message: object
    :param rc: HTTP response code to be returned
    :type rc: int
    :param content_type: String containing the content type declaration
    :type content_type: str

    :return: Tuple containing the json content, response code and content type
    :rtype: tuple
    """
    success = success if success is not None else True
    message = message if message is not None else ""
    rc = rc if rc is not None else 200
    content_type = content_type if content_type is not None else 'application/json'
    return json.dumps({'success': success, 'message': message}), rc, {'ContentType': content_type}


def abort_with_message(message, logger, service_name, services_log_dir, exception=None, http_status_code=500):
    """
    Raise HTTP Exception, with message, to caller

    :param http_status_code: HTTP status code
    :type http_status_code: int
    :param logger: Logger instance provided by the calling service
    :type logger: `log.logger`
    :param service_name: Name of the calling service
    :type service_name: str
    :param services_log_dir: Service log location
    :type services_log_dir: str
    :param message: Error Message
    :type message: str
    :param exception: Exception raised
    :type exception: `Exception`

    """
    exception_text = str(exception) if exception else ""
    error_message = ("{0} - error encountered :: {1} - see {2} service log for more details ({3}/{2}.log)"
                     .format(message, exception_text, service_name, services_log_dir))
    logger.debug("{0}\n{1}".format(error_message, traceback.format_exc()))
    abort(http_status_code, error_message)


def create_and_start_background_scheduled_job(func, time_interval_mins, job_id, logger):
    """
    Create and start a background scheduled job

    :param func: Function to be passed to the background job
    :type func: object
    :param time_interval_mins: Time interval in mins the job should execute
    :type time_interval_mins: int
    :param job_id: Id of the background job
    :type job_id: str
    :param logger: Logger instance provided by the calling service
    :type logger: `log.logger`

    :return: Job created by the scheduler
    :rtype: Job
    """
    logger.info("Creating background scheduled job to execute every {0} mins(s).".format(time_interval_mins))
    scheduler = BackgroundScheduler(daemon=True, timezone=get_time_zone())
    job = scheduler.add_job(func, 'interval', minutes=time_interval_mins, id=job_id)
    logger.info("Background scheduled job created.")
    scheduler.start()
    return job


def create_and_start_once_off_background_scheduled_job(func, job_id, logger, func_args=None):
    """
    Create and start a quick starting background scheduled job, to shutdown after a single run.

    :param func: Function to be passed to the background job
    :type func: object
    :param job_id: Id of the background job
    :type job_id: str
    :param logger: Logger instance provided by the calling service
    :type logger: `log.logger`
    :param func_args: Arguments to be passed to the call to add job
    :type func_args: list|tuple
    """
    logger.info("Creating once off background scheduled job to execute once.")
    scheduler = BackgroundScheduler(daemon=True, timezone=get_time_zone())
    scheduler.add_job(func, id=job_id, args=func_args)
    scheduler.add_job(shutdown_scheduled_job, args=[scheduler, logger])
    logger.info("Background scheduled job created.")
    scheduler.start()


def shutdown_scheduled_job(scheduler, logger):
    """
    Shutdown the supplied scheduler job

    :param scheduler: Instance of BackgroundScheduler to be shutdown
    :type scheduler: `BackgroundScheduler`
    :param logger: Logger instance provided by the calling service
    :type logger: `log.logger`
    """
    logger.info('Once off background scheduled job triggered, shutting down job.')
    scheduler.shutdown(wait=False)
    logger.info('Once off background scheduled job shutdown completed.')


def get_time_zone():
    """
    Determine the system time zone

    :return: Output of the system configuration time zone or default to Europe/Dublin
    :rtype: str
    """
    rc, output = commands.getstatusoutput('grep ZONE /etc/sysconfig/clock')
    if not rc and output:
        return output.split('=')[-1].replace('"', '')
    else:
        return 'Europe/Dublin'
