#!/bin/bash

# DDC plugin for workload profiles

TASK=$1
OUTPUT_DIR=$2

PEM_FILE_NAME="enm_keypair.pem"
PEM_DIR="/var/tmp"
CU_KEY_FILE_WLVM="$PEM_DIR/$PEM_FILE_NAME"
CU_KEY_FILE_EMP="$PEM_DIR/.$PEM_FILE_NAME"
SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SSH_TO_EMP_COMMAND="ssh -t -i $CU_KEY_FILE_WLVM $SSH_OPTIONS cloud-user"
SSH_TO_ESMON_COMMAND="ssh -t -i $CU_KEY_FILE_EMP $SSH_OPTIONS cloud-user"
ROOT_SSH_PRIVATE_KEY_FILE="/root/.ssh/id_rsa"
ROOT_SSH_AUTHORIZED_KEYS_FILE="/root/.ssh/authorized_keys"
ROOT_SSH_PUBLIC_KEY_FILE="$ROOT_SSH_PRIVATE_KEY_FILE.pub"
DYNAMIC_CONTENT_DIR="/home/enmutils/dynamic_content"
INITIAL_PROFILE_SUMMARY="${OUTPUT_DIR}/workload/.initial_profile_summary"

QUOTES="\""
SLASH1="\\"
SLASH3="\\\\\\"
SLASH7="\\\\\\\\\\\\\\"

# sourcing the .bashrc file to read variables EMP & LMS_HOST, if set
source /root/.bashrc

get_initial_profile_summary_from_workload_status_command() {

        if [[ ! -f ${INITIAL_PROFILE_SUMMARY} ]]; then
            if [[ ! -d ${DYNAMIC_CONTENT_DIR} ]]; then
                mkdir -p ${DYNAMIC_CONTENT_DIR}
            fi
            workload_status_report="${DYNAMIC_CONTENT_DIR}/.workload_status_report"
            timestamp=$(echo $(date +'%Y-%m-%d 00:00:00,000'))
            # Take initial workload status snapshot
            /opt/ericsson/enmutils/bin/workload status --no-ansi | egrep _ | egrep -v Password > ${workload_status_report}

            # Populate the INITIAL_PROFILE_SUMMARY file from the output of the workload status report
            while read line; do
                profile_name=$(echo ${line} | awk '{print $1}')
                profile_status=$(echo ${line} | awk '{print $2}')
                message="${timestamp} - INFO - ${profile_name} - Profile state ${profile_status} - Status provided by 'workload status' command"
                echo ${message} >> ${INITIAL_PROFILE_SUMMARY}
            done < ${workload_status_report}
            rm -f ${workload_status_report}
        fi

}

store_profiles_log_info_in_ddc_plugin_data_folder() {

        get_initial_profile_summary_from_workload_status_command

        # Extract profile entries for current day from profiles.log and store in DDC dir
        # (Each entry needs to be sanitized to include ascii/text based info only as otherwise DDP cannot parse the data)
        ascii_regex="s/[^[:ascii:]]//g"
        perl_command="perl -pe $ascii_regex"

        date_regex="^$(date +%Y-%m-%d)"
        egrep_command="egrep --text $date_regex /var/log/enmutils/profiles.log"

        profiles_log="${OUTPUT_DIR}/workload/profiles.log"

        [[ -f /var/log/enmutils/profiles.log ]] && ${egrep_command} | ${perl_command} >  ${profiles_log}.tmp
        [[ -f ${INITIAL_PROFILE_SUMMARY} && -f ${profiles_log}.tmp ]] && cat ${INITIAL_PROFILE_SUMMARY} ${profiles_log}.tmp > ${profiles_log}
        [[ -f ${profiles_log}.tmp ]] && rm -f ${profiles_log}.tmp
}

store_workload_operations_log_info_in_ddc_plugin_data_folder() {
        # Extract entries for current day from workload_operations.log and store in DDC dir

        SOURCE_FILE="/var/log/enmutils/workload_operations.log"

        DDC_PLUGIN_DIR="$OUTPUT_DIR/workload"
        DEST_FILE="$DDC_PLUGIN_DIR/$(basename $SOURCE_FILE)"
        extract_entries_for_today="egrep --text ^$(date +%Y-%m-%d)"
        ascii_regex="s/[^[:ascii:]]//g"
        remove_non_ascii_chars="perl -pe $ascii_regex"

        [[ -f $SOURCE_FILE ]] && $extract_entries_for_today $SOURCE_FILE | $remove_non_ascii_chars > "$DEST_FILE"

}

store_cmsync_workload_log_info_in_ddc_plugin_data_folder() {
        # Extract entries for current day from /home/enmutils/cm/cmsync_ddp_info.log and store in DDC dir

        SOURCE_FILE="/home/enmutils/cm/cmsync_ddp_info.log"

        DDC_PLUGIN_DIR="$OUTPUT_DIR/workload"
        DEST_FILE="$DDC_PLUGIN_DIR/$(basename $SOURCE_FILE)"
        extract_entries_for_today="egrep --text ^$(date +%Y/%m/%d)"
        ascii_regex="s/[^[:ascii:]]//g"
        remove_non_ascii_chars="perl -pe $ascii_regex"

        [[ -f $SOURCE_FILE ]] && $extract_entries_for_today $SOURCE_FILE | $remove_non_ascii_chars > "$DEST_FILE"

}

store_cmimport_workload_log_info_in_ddc_plugin_data_folder() {
        # Extract entries for import profiles from /home/enmutils/cm/cmimport_ddp_info.log and store in DDC dir

        SOURCE_FILE="/home/enmutils/cm/cmimport_ddp_info.log"

        DDC_PLUGIN_DIR="$OUTPUT_DIR/workload"
        DEST_FILE="$DDC_PLUGIN_DIR/$(basename $SOURCE_FILE)"
        extract_entries_for_today="egrep --text ^$(date +%Y/%m/%d)"
        ascii_regex="s/[^[:ascii:]]//g"
        remove_non_ascii_chars="perl -pe $ascii_regex"

        [[ -f $SOURCE_FILE ]] && $extract_entries_for_today $SOURCE_FILE | $remove_non_ascii_chars > "$DEST_FILE"

}
store_redis_info_in_ddc_plugin_data_folder() {

        # Extract entries for current day from redis_monitoring.log and store in DDC dir
        redis_monitor_log_source="/var/log/enmutils/redis/redis_monitoring.log"
        redis_monitor_log_ddc="${OUTPUT_DIR}/workload/redis_monitoring_log_info"

        date_regex="^### $(date +%y%m%d)"
        extract_entries_for_today="\$s = True if /$date_regex/; print if \$s"
        [[ -f ${redis_monitor_log_source} ]] && perl -ne "${extract_entries_for_today}" ${redis_monitor_log_source} > ${redis_monitor_log_ddc}
}

store_torutils_package_revision_info_in_ddc_plugin_data_folder() {

        # Get TorUtils current version and version history and store info in DDC dir
        [[ -f /etc/torutils-history ]] && cp -p /etc/torutils-history ${OUTPUT_DIR}/workload/
        rpm -qa | egrep ERICtorutilitiesinternal > ${OUTPUT_DIR}/workload/torutils-version
}

store_workload_artefacts_in_ddc_plugin_data_folder() {

    if [[ -d ${OUTPUT_DIR} ]]; then
        logOutput "Creating workload log files"
        mkdir -p ${OUTPUT_DIR}/workload

        store_profiles_log_info_in_ddc_plugin_data_folder

        store_workload_operations_log_info_in_ddc_plugin_data_folder

        store_redis_info_in_ddc_plugin_data_folder

        store_torutils_package_revision_info_in_ddc_plugin_data_folder

        store_cmimport_workload_log_info_in_ddc_plugin_data_folder

        store_cmsync_workload_log_info_in_ddc_plugin_data_folder

        logOutput "Workload log files created"
    fi
}

constructRemoteCommand() {
    COMMAND=$1
    esmon_command="$SLASH1$QUOTES sudo sh -c $SLASH3$QUOTES${COMMAND} $SLASH3$QUOTES $SLASH1$QUOTES"
    emp_command="$QUOTES$SSH_TO_ESMON_COMMAND@esmon $esmon_command $QUOTES"
    remote_command="$SSH_TO_EMP_COMMAND@${EMP} ${emp_command} 2>/dev/null"
    echo "$remote_command"
}

setCloudUserSshPrivateKeyPermissions() {
    command="chmod 600 $CU_KEY_FILE_WLVM"
    failed_message="Failed to set permissions on cloud-user ssh private key"
    bash -c "$command"
    [[ $? == 0 ]] && echo "Success" || echo "$failed_message - command: $command"
}

copyCloudUserSshPrivateKeyToEmp() {
    command="scp -q -i $CU_KEY_FILE_WLVM $SSH_OPTIONS $CU_KEY_FILE_WLVM cloud-user@$EMP:$CU_KEY_FILE_EMP"
    failed_message="Failed to copy cloud-user ssh key to EMP to allow plugin to connect to ESMON via ssh"
    bash -c "$command"
    [[ $? == 0 ]] && echo "Success" || echo "$failed_message - command: $command"
}

checkIfEsmonRootSshPublicKeyFileExists() {
    command="[ -f $ROOT_SSH_PUBLIC_KEY_FILE ] && echo True || echo False"
    remote_command=$(constructRemoteCommand "$command")
    [[ $(bash -c "$remote_command " | egrep -c True) -eq 1 ]] && echo "True" || echo "False"
}

getEsmonRootSshPublicKey() {
    command="cat $ROOT_SSH_PUBLIC_KEY_FILE"
    remote_command=$(constructRemoteCommand "$command")
    message="${QUOTES}Connection to .* closed${QUOTES}"
    echo $(bash -c "$remote_command | sed ${QUOTES}s/\r/\n/g${QUOTES} | egrep -v $message | egrep esmon")
}

generateEsmonRootSshPublicKey() {
    command="/usr/bin/ssh-keygen -t rsa -f $ROOT_SSH_PRIVATE_KEY_FILE -N $SLASH7$QUOTES$SLASH7$QUOTES>/dev/null"
    remote_command=$(constructRemoteCommand "$command")
    echo $(bash -c "$remote_command" > /dev/null)
}

fetchAndStoreEsmonSshPublicKey() {
    if [[ -f ${CU_KEY_FILE_WLVM} ]]; then
        set_permissions_result=$(setCloudUserSshPrivateKeyPermissions)
        if [[ "$set_permissions_result" != "Success" ]]; then
                echo ${set_permissions_result}
                exit 1
        fi

        key_copy_result=$(copyCloudUserSshPrivateKeyToEmp)
        if [[ "$key_copy_result" != "Success" ]]; then
                echo ${key_copy_result}
                exit 1
        fi

        if [[ "$(checkIfEsmonRootSshPublicKeyFileExists)" == "False" ]]; then
                logOutput "Generating public key on esmon"
                generateEsmonRootSshPublicKey
        fi

        public_key=$(getEsmonRootSshPublicKey)
        if [[ $(echo "$public_key" | egrep -c "esmon") -eq 1 ]]; then
                if [[ ! -e ${ROOT_SSH_AUTHORIZED_KEYS_FILE} ]] ; then
                        touch ${ROOT_SSH_AUTHORIZED_KEYS_FILE}
                fi

                if [[ -f ${ROOT_SSH_AUTHORIZED_KEYS_FILE} ]]; then
                        if [[ $(grep -c "$public_key" ${ROOT_SSH_AUTHORIZED_KEYS_FILE}) -ne 1 ]]; then
                                logOutput "Adding esmon public key to authorized keys on this server"
                                sed -i "/esmon/d" ${ROOT_SSH_AUTHORIZED_KEYS_FILE}
                                echo ${public_key} >> ${ROOT_SSH_AUTHORIZED_KEYS_FILE}
                        fi
                fi
        fi
    fi
}

processWorkloadLogFiles() {
    logOutput "Processing workload log files started"
    store_workload_artefacts_in_ddc_plugin_data_folder

    if [[ -z "$EMP" && -z "$LMS_HOST" ]]; then
        logOutput "Increment file processing started (cENM)"
        /opt/ericsson/enmutils/bin/utilities ddc_plugin_create_increment_files
        logOutput "Increment file processing complete"
    fi
    logOutput "Processing workload log files complete"
}

updateAuthorizedKeysVENM() {
    # Cloud ENM deployment only:-
    [[ "$EMP" != "" ]] && fetchAndStoreEsmonSshPublicKey
}

noAction() {
    logOutput "No actions to be performed"
}

logOutput() {
  message=$1
  echo "$(date +'%Y-%m-%d %H:%M:%S') INFO: DDC plugin for Workload: ($TASK) $message"
}

case "${TASK}" in
    START)
        noAction
        ;;
    STOP)
        processWorkloadLogFiles
        ;;
    TRIGGER)
        updateAuthorizedKeysVENM
        ;;
    MAKETAR)
        processWorkloadLogFiles
        ;;
    DELTA)
        processWorkloadLogFiles
        ;;
esac

exit 0
