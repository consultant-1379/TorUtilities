import os
import pkgutil


# POSSIBLE ENVIRON VALUES
# "production", "local", "testing", "jenkins"
ENVIRON = "jenkins"

LOCAL_DIR = os.path.join(pkgutil.get_loader('enmutils').filename, '..')  # Hardcoded for localhost and testing environments
REDIS_DB_INDEX = 34  # jenkins index as per https://eteamspace.internal.ericsson.com/display/ERSD/The+Team
