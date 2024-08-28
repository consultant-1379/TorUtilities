from collections import namedtuple
# Deprecated 20.11 To Be Deleted 21.06 RTD-13702

System = namedtuple('System', ['name', 'user', 'ip', 'password', 'commands_file', 'active'])

#  Not really using this anymore in any automated runs.
#  Don't expect vapps info to be updated to often - as this info is being send around by the tester

Systems = {}
# Loop through all systems above and return the systems that are enabled
Enabled = dict((k, v) for k, v in Systems.items() if v.active is True)
