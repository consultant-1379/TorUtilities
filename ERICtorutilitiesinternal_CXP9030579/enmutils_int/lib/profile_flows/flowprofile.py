from enmutils_int.lib.profile import Profile


class FlowProfile(Profile):

    def __init__(self, *args, **kwargs):
        self.NAME = self.__class__.__name__
        super(FlowProfile, self).__init__(*args, **kwargs)

    def run(self):
        pass
