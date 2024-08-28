# ********************************************************************
# Name    : Headers
# Summary : Contains importable REST header data.
# ********************************************************************

SECURITY_REQUEST_HEADERS = {"X-Requested-With": "XMLHttpRequest"}
DELETE_SECURITY_REQUEST = {"X-Requested-With": "XMLHttpRequest", "If-Match": "*"}
JSON_SECURITY_REQUEST = {"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json", "Accept": "application/json"}
PMIC_REST_NBI_JSON_SECURITY_REQUEST = {"Content-Type": "application/json", "Accept": "application/json"}
FLS_HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
SHM_LONG_HEADER = {
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
}
NETEX_HEADER = dict({"X-Tor-Application": "networkexplorer"}, **JSON_SECURITY_REQUEST)
NETEX_COLLECTION_HEADER = dict({"X-Tor-Application": "networkexplorercollections"}, **JSON_SECURITY_REQUEST)
NETEX_IMPORT_HEADER = dict({"X-Tor-Application": "networkexplorercollections"}, **SECURITY_REQUEST_HEADERS)

JSON_HEADER = {"Content-Type": "application/json; charset=utf-8"}

PLM_IMPORT_REQUEST_HEADER = {"X-Requested-With": "XMLHttpRequest",
                             "Accept": "application/json, text/javascript, */*",
                             "X-Tor-Application": "linkmanagement"}
ASU_CREATE_FLOW_HEADER = {'Accept': 'application/json',
                          'cache-control': 'no-cache'}
ASU_STATUS_FLOW_HEADER = {"X-Requested-With": "XMLHttpRequest",
                          'Accept': 'application/json, text/javascript, */*; q=0.01',
                          "Accept-Encoding": "gzip, deflate, br",
                          "Accept-Language": "en-US,en;q=0.9",
                          "X-Tor-Application": "flow-instance-details"}
CRUD_PATCH_HEADER = {"Content-Type": "application/3gpp-json-patch+json"}

DYNAMIC_CRUD_PUT_HEADER = {"Content-Type": "application/merge-patch+json"}

CMEVENT_HEADERS = {"Content-Type": "application/json", "Accept": "application/hal+json"}
