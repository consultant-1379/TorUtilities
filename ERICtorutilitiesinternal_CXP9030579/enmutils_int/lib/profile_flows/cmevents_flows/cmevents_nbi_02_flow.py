from functools import partial
import time
import re
import pexpect
import requests
from requests.exceptions import RequestException
from enmutils.lib import headers, log, config
from enmutils.lib.persistence import picklable_boundmethod
from enmutils.lib.cache import (shell, get_emp, is_host_physical_deployment, CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, is_enm_on_cloud_native)
from enmutils.lib.exceptions import EnvironError
from enmutils.lib.enm_user_2 import raise_for_status

from enmutils_int.lib.dit import get_documents_info_from_dit, get_document_content_from_dit, get_sed_id
from enmutils_int.lib.enm_deployment import get_cloud_members_ip_address
from enmutils_int.lib.profile_flows.common_flows.common_flow import GenericFlow
from enmutils_int.lib.services.deployment_info_helper_methods import get_hostname_cloud_deployment

CN_URL = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get ingress --all-namespaces 2>/dev/null | egrep ui"
EMP_LOGIN_CMD = "ssh -o StrictHostKeyChecking=no -i {2} {0}@{1}"
VNF_LOGIN_CMD = "ssh -i {2} -o stricthostkeychecking=no {0}@{1}"
SUBSCRIPTIONS_URL = "/cm/subscribed-events/v1/subscriptions/"
SUBSCRIPTIONS_ENDPOINT = "/cm/subscribed-events/v1/subscriptions/{0}"
EVENTLISTENER_URL = "http://{0}:8080/eventListener/v1/SUB{1}"
EVENTLISTENER_IP_URL = "https://ci-portal.seli.wh.rnd.internal.ericsson.com/generateTAFHostPropertiesJSON/?clusterId={0}"


class CmEventsNbi02(GenericFlow):
    PAYLOAD = []
    SUBS_IDS = []

    def execute_flow(self):
        self.state = "RUNNING"

        try:
            users = self.create_profile_users(self.NUM_USERS, self.USER_ROLES)
            eventllistener_vm_ip = self.get_eventlistner_vm_ip()
            log.logger.debug("THE EVENTLISTNER_VM IP IS {0}".format(eventllistener_vm_ip))
            for subscriber in range(1, self.NUM_SUBSCRIBERS + 1):
                log.logger.debug("The SUBSCRIBER is {}".format(subscriber))
                eventlistener = EVENTLISTENER_URL.format(eventllistener_vm_ip, subscriber)
                data = {"ntfSubscriptionControl": {"notificationRecipientAddress": eventlistener,
                                                   "scope": {"scopeType": "BASE_ALL"}, "id": "Request_id",
                                                   "objectClass": "/", "objectInstance": "/"}}
                self.PAYLOAD.append(data)

            self.SUBS_IDS = self.read_existing_subscription(users[0], SUBSCRIPTIONS_URL)
            if self.SUBS_IDS:
                log.logger.debug(
                    "THE SUBSCRIPTION ALREADY EXISTS ON THE SYSTEM, SETTING THE PROFILE TO COMPLETED STATE.")
            else:
                self.SUBS_IDS = []
                for payload in self.PAYLOAD:
                    subs_id = self.send_post_request(users[0], SUBSCRIPTIONS_URL, payload)
                    self.read_and_delete(users[0], subs_id, "GET", payload)
                    self.SUBS_IDS.append(subs_id)

            for subs_id in self.SUBS_IDS:
                log.logger.debug("APPENDING SUBSCRIPTION ID {0} to TEARDOWN FOR DELETION ".format(subs_id))
                for payload in self.PAYLOAD:
                    self.teardown_list.append(partial(picklable_boundmethod(self.read_and_delete), user=users[0],
                                                      subs_id=subs_id, operation="DELETE", payload=payload))
                    self.PAYLOAD.remove(payload)

        except Exception as e:
            self.add_error_as_exception(e)

    def get_eventlistner_vm_ip(self):
        """
        Returns the IP address of VM

        :rtype: int
        :return: IP of VM attached to server
        :raises EnvironError: if VM IP is not available on the server.
        """
        log.logger.debug("Fetching the VM IP")
        eventlistener_vm_ip = None
        if is_host_physical_deployment():
            cluster_id = self.fetch_cluster_id_in_physical()
            eventlistener_vm_ip = self.fetch_eventlistener_vm_ip_in_physical(cluster_id)
        elif config.is_a_cloud_deployment():
            cloud_deployment_name = self.get_hostname_of_cloud()
            eventlistener_vm_ip = self.fetch_eventlistener_vm_ip_in_cloud(cloud_deployment_name)
        elif is_enm_on_cloud_native():
            eventlistener_vm_ip = self.fetch_eventlistener_vm_ip_in_cloud_native()
        if not eventlistener_vm_ip:
            raise EnvironError("Eventlistener VM IP not available in deployment")

        return eventlistener_vm_ip

    def send_post_request(self, user, url, payload):
        """
        Makes a POST request to application to create subscription to eventlistener.

        :param user: User who make the POST request to ENM
        :type user: `enm_user_2.User`
        :param url: The URL to be used for the POST request
        :type url: str
        :param payload: The JSON payload to be sent in the POST request
        :type payload: dict
        :rtype: int
        :return: ID of Subscription created on server
        """
        log.logger.debug("SENDING REQUEST FOR ENABLING THE SUBSCRIPTION WITH PAYLOAD {0}".format(payload))
        try:
            response = user.post(url, json=payload, headers=headers.CMEVENT_HEADERS)
            raise_for_status(response, message_prefix="Failed to create subscription: ")
            log.logger.debug("Successfully created the subscription.")
            return response.json()['ntfSubscriptionControl']['id']

        except RequestException as e:
            self.add_error_as_exception(e)

    def read_existing_subscription(self, user, url):
        """
        Reads a subscription

        :param user: User who make the POST request to ENM
        :type user: `enm_user_2.User`
        :param url: The url used to send GET request
        :type url: str
        :rtype: list
        :return: ID of Subscription created on server
        :raises HTTPError: Cannot delete or read the subscription
        """
        subscription_id = []
        try:
            log.logger.debug("SENDING REQUEST TO GET THE INFO OF EXISTING SUBSCRIPTIONS")
            response = user.get(url, headers=headers.CMEVENT_HEADERS)
            raise_for_status(response, message_prefix="Failed to read subscription details: ")

            if response.status_code == 200:
                log.logger.debug("SUCCESSFULLY READ THE SUBSCRIPTION, THE SUBSCRIPTION IS - {0} of status code {1}"
                                 .format(response.json(), response.status_code))
                data_list = response.json()
                for item in data_list:
                    json_response = item['ntfSubscriptionControl']['id']
                    subscription_id.append(json_response)
                log.logger.debug("THE SUBSCRIPTIONS ID ARE {0}".format(subscription_id))
                return subscription_id

            elif response.status_code == 204:
                log.logger.debug("SUCCESSFULLY READ THE SUBSCRIPTION. THERE IS NO SUBSCRIPTION FOUND ON THE SYSTEM "
                                 "Response - {0} of status code {1}".format(response, response.status_code))

        except RequestException as e:
            self.add_error_as_exception(e)

    def read_and_delete(self, user, subs_id, operation, payload):
        """
        Deletes or Reads a subscription

        :param user: User who make the POST request to ENM
        :type user: `enm_user_2.User`
        :param subs_id: The id to be used for the DELETE or GET request
        :type subs_id: str
        :param operation: The type of operation to be performed on subscription
        :type operation: str
        :param payload: The JSON payload to be sent in the POST request
        :type payload: dict
        :raises HTTPError: Cannot delete or read the subscription
        """
        try:
            if operation == "DELETE":
                log.logger.debug("Sending delete request for disabling the subscription")
                response = user.delete_request(SUBSCRIPTIONS_ENDPOINT.format(subs_id), json=payload,
                                               headers=headers.CMEVENT_HEADERS)
                raise_for_status(response, message_prefix="Failed to delete subscription: ")
                log.logger.debug("Successfully deleted the subscription with id - {0}".format(subs_id))
            else:
                log.logger.debug("Sending get request to read info of the subscription")

                response = user.get(SUBSCRIPTIONS_ENDPOINT.format(subs_id), json=payload,
                                    headers=headers.CMEVENT_HEADERS)
                raise_for_status(response, message_prefix="Failed to read subscription details: ")
                log.logger.debug("Successfully read the subscription with id - {0}, Response - {1}".format(
                    subs_id, response.json()))
        except RequestException as e:
            self.add_error_as_exception(e)

    def fetch_cluster_id_in_physical(self):
        """
        Check in physical environment and fetch deployment Cluster ID.

        :rtype: Int
        :return: Cluster ID of the deployment
        :raises EnvironError: if Cluster ID is retrieved
        """
        try:
            command = "crontab -l"
            response = shell.run_cmd_on_ms(command)
            if "-s" in response.stdout:
                deployment_name = response.stdout.split("-s")[1].split()[0]
                if "ENM" in deployment_name:
                    cluster_id = deployment_name.split("M")[1]
                else:
                    cluster_id = deployment_name
            else:
                raise EnvironError("Issue occurred while fetching deployment name using crontab -l/ddc_upload."
                                   " Check and also the deployment name is emp is not correct.")
            log.logger.debug("Cluster ID fetch from deployment {0} is : {1}".format(deployment_name, cluster_id))

            return cluster_id

        except Exception as e:
            self.add_error_as_exception(e)

    def fetch_eventlistener_vm_ip_in_physical(self, cluster_id):
        """
        Fetch eventlistener vm ip using url of ci-portal.

        :rtype: string
        :return: deployment name
        :raises EnvironError: if the output is not ok
        """
        log.logger.debug("Fetching eventlistener vm ip from DMT using url")
        response = requests.get(EVENTLISTENER_IP_URL.format(cluster_id), verify=False)
        if response.status_code == 200:
            json_data = response.json()
            event_listener_data = next((data for data in json_data if data['hostname'] == 'eventlistener'), None)
            if event_listener_data:
                public_interface = next(
                    (interface for interface in event_listener_data['interfaces'] if interface['type'] == 'public'),
                    None)
                if public_interface:
                    public_ipv4 = public_interface['ipv4']
                    log.logger.debug("IPv4 address for 'eventlistener' public interface:{0}".format(public_ipv4))
                else:
                    raise EnvironError("No 'public' interface found for 'eventlistener'.")
            else:
                raise EnvironError("No block with hostname 'eventlistener' found.")
        else:
            raise EnvironError("Failed to retrieve data. Status code: {0}".format(response.status_code))

        return public_ipv4

    def get_hostname_of_cloud(self):
        """
        Check in cloud environment and fetch deployment_hostname.

        :rtype: string
        :return: deployment_hostname
        :raises EnvironError: if the output is not ok
        """
        try:
            _, deployment_hostname = get_hostname_cloud_deployment()
            sed_id = get_sed_id(deployment_hostname)
            if not sed_id:
                deployment_hostname = self.fetch_deployment_name_in_cloud()
            log.logger.debug("Deployment name in cloud server {0}".format(deployment_hostname))
            return deployment_hostname
        except Exception as e:
            self.add_error_as_exception(e)

    def fetch_deployment_name_in_cloud(self):
        """
        Check in cloud environment and fetch deployment name.

        :rtype: string
        :return: deployment name
        :raises EnvironError: if the output is not ok
        """
        log.logger.debug("Fetching deployment name in cloud server")
        retry = 1
        max_retries = 3
        while retry <= max_retries:
            vnflaf = get_cloud_members_ip_address('vnflaf')
            cmd = EMP_LOGIN_CMD.format('cloud-user', get_emp(), CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_WL_VM, timeout=30)
            with pexpect.spawn(cmd) as child:
                vnf_cmd = VNF_LOGIN_CMD.format('cloud-user', vnflaf[0], CLOUD_USER_SSH_PRIVATE_KEY_FILE_ON_EMP,
                                               timeout=30)
                child.expect(['cloud-user@', pexpect.EOF, pexpect.TIMEOUT])
                child.sendline(vnf_cmd)
                child.expect(['cloud-user@', pexpect.EOF, pexpect.TIMEOUT])
                child.sendline('sudo su')
                child.expect(['root@', pexpect.EOF, pexpect.TIMEOUT])
                deployment = child.before
                log.logger.debug("Output of server after executing command {0}".format(deployment))
                deployment_name = deployment.split('-')[0]
                log.logger.debug("Deployment name: {0}".format(deployment_name))
                child.terminate()
            sed_id = get_sed_id(deployment_name)
            if not sed_id:
                log.logger.debug("Getting deployment for cloud vio server")
                deployment_name = deployment[:8]
                log.logger.debug("Deployment name of cloud vio server:{0}".format(deployment_name))
                sed_id = get_sed_id(deployment_name)
                if not sed_id:
                    deployment_name = str('vio_') + str(deployment_name.split('-')[-1])
                    log.logger.debug("Deployment name of vio for wrong dit name format:{0}".format(deployment_name))
                    sed_id = get_sed_id(deployment_name)
            if sed_id:
                return deployment_name
            else:
                retry += 1
                log.logger.info("Sleeping for 300 secs before retrying to connect the VNF")
                time.sleep(300)

    def fetch_eventlistener_vm_ip_in_cloud(self, cloud_deployment_name):
        """
        First get the deployment name and then fetch eventlistener vm ip from DIT.

        :rtype: string
        :return: deployment name
        :raises EnvironError: if the output is not ok
        """
        log.logger.debug("The cloud deployment name : {0}".format(cloud_deployment_name))
        document_info_dict = get_documents_info_from_dit(cloud_deployment_name)
        deployment_doc_number = document_info_dict.get("CM_Subscribed_Events_Event_Listener")
        if deployment_doc_number:
            deployment_document_content = get_document_content_from_dit(deployment_doc_number)
            eventlistener_vm_ip = deployment_document_content.get("parameters").get("EVENTLISTENER")
            if eventlistener_vm_ip:
                return eventlistener_vm_ip
            else:
                raise EnvironError("EVENTLISTENER VM IP not available.")
        else:
            raise EnvironError(
                "CM_Subscribed_Events_Event_Listener document not attached to DIT to fetch 'eventlistener' IP.")

    def fetch_deployment_name_cnis(self, response):
        """
        fetch deployment name from DIT.

        :rtype: string
        :return: deployment name
        """
        match = re.search(r'[\d]{3}', response)
        if match is not None:
            log.logger.debug("deployment name from {0}".format('cnisenm' + match.group()))
            return 'cnisenm' + match.group()

    def fetch_eventlistener_vm_ip_in_cloud_native(self):
        """
        First get the deployment name and then fetch eventlistener vm ip from DIT.

        :rtype: string
        :return: deployment name
        :raises EnvironError: if the output is not ok
        """
        log.logger.debug("Fetching EVENTLISTNER VM IP in cloud native deployment")
        response = shell.run_local_cmd(shell.Command(CN_URL))
        if not response.stdout:
            raise EnvironError("Issue occurred while fetching deployment name using kubectl command. "
                               "check maunally on wlvm by executing command {0}".format(CN_URL))
        deployment_name = response.stdout.split()[3].split(".")[0]
        sid_id = get_sed_id(deployment_name)
        if sid_id is None:
            deployment_name = self.fetch_deployment_name_cnis(response.stdout)
        document_info_dict = get_documents_info_from_dit(deployment_name)
        eventlistener_doc_number = document_info_dict.get("CM_Subscribed_Events_Event_Listener")
        if eventlistener_doc_number:
            document_content = get_document_content_from_dit(eventlistener_doc_number)
            eventlistener_vm_ip = document_content.get("parameters").get("EVENTLISTENER")
            if eventlistener_vm_ip:
                return eventlistener_vm_ip
            else:
                raise EnvironError("EVENTLISTENER VM IP not available.")
        else:
            raise EnvironError(
                "CM_Subscribed_Events_Event_Listener document not attached to DIT to fetch 'eventlistener' IP.")
