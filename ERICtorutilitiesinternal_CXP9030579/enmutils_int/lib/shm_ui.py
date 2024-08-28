# ********************************************************************
# Name    : SHM UI
# Summary : Functional module used for interacting with SHM URI via
#           RESTful requests. Allows the user to perform UI requests,
#           such as home page, help, UI views such as software,
#           hardware, licensing pages.
# ********************************************************************

import json

from requests.exceptions import HTTPError

HEADERS = {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json, text/javascript, */*; q=0.01'}


def shm_home(user):
    """Visit the shm home page
        :param user: `lib.enm_user.User` instance
    """
    home_url = '/#shm'
    response = user.get(home_url, verify=False)
    return response


def shm_view_inventory(user):
    """ Generic GET request avaialble to sw/hw/licence/backup
        :param user: `lib.enm_user.User` instance
    """
    view_inv_url = 'oss/shm/rest/inventory/rbac/viewinventory'
    response = user.get(view_inv_url, verify=False)
    return response.status_code


def shm_license_inventory_home(user):
    """Visit the shm license inventory page
        :param user: `lib.enm_user.User` instance
    """
    license_home_url = '/#shm/licenseadministration'
    response = user.get(license_home_url, verify=False)
    return response.status_code


def shm_license_go_to_topology_browser(user):
    """ Navigate to topology browser.
        :param user: `lib.enm_user.User` instance
    """
    topology_home_url = "/#networkexplorer?goto=shmlicenseinventory%2FloadNodes&returnType=multipleObjects"
    response = user.get(topology_home_url, verify=False)
    return response.status_code


def shm_import_license_keys(user):
    """Visit the shm software administration page
        :param user: `lib.enm_user.User` instance
    """
    import_keys_url = '/#shm/licenseadministration/importlicensekeyfiles'
    response = user.get(import_keys_url, verify=False)
    return response.status_code


def shm_software_administration_home(user):
    """Visit the shm software administration page
        :param user: `lib.enm_user.User` instance
    """
    software_home_url = '/#shm/softwareadministration'
    user.get(software_home_url, verify=False)


def shm_software_administration_upgrade_tab(user):
    """Visit the shm software administration page
       and the Software Packages tab
            :param user: `lib.enm_user.User` instance
    """
    software_upgrade_packages_home_url = '/#shm/softwareadministration/softwarepackages'
    user.get(software_upgrade_packages_home_url, verify=False)


def shm_import_software_package(user):
    """Visit the shm software administration page
        :param user: `lib.enm_user.User` instance
    """
    import_software_url = '/#shm/softwareadministration/importsoftwarepackages'
    user.get(import_software_url, verify=False)


def shm_software_go_to_topology_browser(user):
    """ Navigate to topology browser.
        :param user: `lib.enm_user.User` instance
    """
    topology_home_url = "/#networkexplorer?goto=shmsoftwareinventory%2FloadNodes&returnType=multipleObjects"
    user.get(topology_home_url, verify=False)


def shm_software_help(user):
    """Browse the shm software help pages
        :param user: `lib.enm_user.User` instance
    """
    user.get('/#help/app/importsoftwarepackages')
    user.get('/#help/app/importsoftwarepackages/concept/tutorials/map')
    user.get('/#help/app/importsoftwarepackages/concept/ui')


def shm_hardware_administration_home(user):
    """ Navigate to Hardware Administration page.
        :param user: `lib.enm_user.User` instance
    """
    topology_home_url = "/#shm/hardwareadministration"
    user.get(topology_home_url, verify=False)


def shm_hardware_go_to_topology_browser(user):
    """ Navigate to topology browser.
        :param user: `lib.enm_user.User` instance
    """
    topology_home_url = "/#networkexplorer?goto=shmhardwareinventory%2FloadNodes&returnType=multipleObjects"
    user.get(topology_home_url, verify=False)


def shm_backup_administration_home(user):
    """Visit the shm software administration page
        :param user: `lib.enm_user.User` instance
    """
    software_home_url = '/#shm/backupadministration'
    user.get(software_home_url, verify=False)


def shm_backup_go_to_topology_browser(user):
    """ Navigate to topology browser.
        :param user: `lib.enm_user.User` instance
    """
    topology_home_url = "/#networkexplorer?goto=shmbackupinventory%2FloadNodes&returnType=multipleObjects"
    user.get(topology_home_url, verify=False)


def view_job_details(user, job):
    """View specific job details
        :param user: `lib.enm_user.User` instance
        :param job: Job object from which we can get the job id
    """
    job_details_url = "#shm/jobdetails/{id}"
    user.get(job_details_url.format(id=job.job_id), verify=False)


def view_job_logs(user, job):
    """View specific job logs
        :param user: `lib.enm_user.User` instance
        :param job: Job object from which we can get the node list
    """
    view_logs_url = "#shm/jobdetails/joblogs/{0}"
    user.get(view_logs_url.format(",".join([node.node_id for node in job.nodes])), verify=False)


def download_logs(user):
    """Download the logs from the shm jobs
        :param user: `lib.enm_user.User` instance
    """
    download_logs_url = "oss/shm/rest/rbac/exportjoblogs"
    user.get(download_logs_url, verify=False)


def return_nodes_to_shm_app(user, nodes):
    """return nodes
        :param user: `lib.enm_user.User` instance
        :param nodes: list of `lib.enm_node.Node`
    """
    while nodes:
        endpoint = "/managedObjects/getPosByPoIds"
        payload = {
            "attributeMappings": [
                {
                    "moType": "NetworkElement",
                    "attributeNames": [
                        "neType", "platformType"
                    ]
                }
            ],
            "poList": [node.poid for node in nodes[0:250]]
        }
        response = user.post(endpoint, headers=HEADERS, data=json.dumps(payload))
        if not response.ok:
            raise HTTPError(
                'Cannot get nodes from Network Explorer. Check logs for details. Response was "%s"'
                % response.text, response=response)
        nodes = nodes[250:]
