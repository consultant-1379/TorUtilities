from collections import OrderedDict

ONCE_OFF_BEFORE_STABILITY = OrderedDict()
SETUP = OrderedDict()
EXCLUSIVE = OrderedDict()
NON_EXCLUSIVE = OrderedDict()
PLACEHOLDERS = OrderedDict()

# The following is a schedule template file.
# Do not edit any of the variable names above. (ONCE_OFF_BEFORE_STABILITY,SETUP,EXCLUSIVE,NON_EXCLUSIVE)
# Group profiles into any of the following categories:
# ONCE_BEFORE_STABILITY: Profiles which should be ran once before any other workload is kicked off.
# EXCLUSIVE: Grouped by application, these profiles require exclusive nodes which will not be affected by other profiles
# SETUP: Any profile which is needed as a prerequisite before workload is applied to a specific application.
# NON_EXCLUSIVE: Grouped by application, these profiles can use any of the other non-exclusive nodes in the node pool.

# APPLICATION           PROFILES                                                     START_SLEEP,  STOP_SLEEP(SEC)

once_before_stability = ONCE_OFF_BEFORE_STABILITY["ONCE_BEFORE_STABILITY"] = OrderedDict()

once_before_stability["<PROFILE_A>"] =                                                      (20,     10)

# ---------------------------------------------------------------------------------------------------------------

exclusive = EXCLUSIVE["EXCLUSIVE"] = OrderedDict()

exclusive["<PROFILE_B>"] =                                                                  (5,      10)

# ---------------------------------------------------------------------------------------------------------------

setup = SETUP["SETUP"] = OrderedDict()

setup["PROFILE_SETUP"] =                                                                    (5,      10)

# ---------------------------------------------------------------------------------------------------------------

app_1 = NON_EXCLUSIVE["APP_1"] = OrderedDict()

app_1["PROFILE_C"] =                                                                        (10,    10)

# ---------------------------------------------------------------------------------------------------------------

app_2 = NON_EXCLUSIVE["APP_2"] = OrderedDict()

app_2["PROFILE_D"] =                                                                        (10,    10)

# ---------------------------------------------------------------------------------------------------------------

# DO NOT EDIT BELOW #
WORKLOAD = [ONCE_OFF_BEFORE_STABILITY, EXCLUSIVE, SETUP, NON_EXCLUSIVE]