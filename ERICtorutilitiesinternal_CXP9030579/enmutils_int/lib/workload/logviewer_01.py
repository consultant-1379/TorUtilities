from enmutils_int.lib.profile_flows.logviewer_flows.logviewer_flow import LogViewerFlow


class LOGVIEWER_01(LogViewerFlow):

    """
    Use Case id:        LogViewer_01
    Slogan:             LogViewer Operator Load
    """

    NAME = "LOGVIEWER_01"

    def run(self):
        self.execute_flow()


logviewer_01 = LOGVIEWER_01()
