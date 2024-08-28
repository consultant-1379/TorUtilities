# ********************************************************************
# Name    : Test Settings
# Summary : Contains settings required to perform tests
# ********************************************************************

UPDATE_NEXUS_URL_COMMAND = ("echo 'Update NEXUS URLs'; "
                            "for FILE in $(egrep -r arm101-eiffel004.lmera /opt/ericsson/enmutils/ 2>/dev/null | "
                            "egrep .py: | egrep -v test | awk -F':' '{print $1}'); do /bin/cp -p $FILE $FILE.orig; "
                            "sed -i 's/arm101-eiffel004.lmera/arm1s11-eiffel004.eiffel.gic/' $FILE; done")
