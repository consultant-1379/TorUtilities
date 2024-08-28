import os
import pkgutil


# POSSIBLE ENVIRON VALUES
# "production", "local", "testing", "jenkins"
ENVIRON = "local"

LOCAL_DIR = os.path.join(pkgutil.get_loader('enmutils').filename, '..', '..')  # Hardcoded for localhost and testing environments
REDIS_DB_INDEX = 0  # Change this to use your own local index on testing servers
