EXECUTE_AMOS_SCRIPT = "kubectl -n {0} exec -it {1} -- bash"
CHECK_SERVICES_CMD_ON_CN = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get pods -n {0} | grep -i {1} " \
                           "| grep -i running"
COPY_FILES = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config cp {source_machine}{source_file} " \
             "{destination_machine}{dest_file} 2>/dev/null"
CREATE_POD_ON_CN = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config apply -f {0} -n {1}"
DELETE_POD_ON_CN = "/usr/local/bin/kubectl delete pod {0} -n {1}"
DELETE_STATEFULSET_POD_ON_CN = "/usr/local/bin/kubectl delete statefulset {0} -n {1}"
CHECK_CONFIGMAP_CMD_ON_CN = "/usr/local/bin/kubectl --kubeconfig /root/.kube/config get cm -n {0} |grep -i {1}"
DELETE_K8S_OBJECTS = "/usr/local/bin/kubectl delete -f {0} -n {1}"
