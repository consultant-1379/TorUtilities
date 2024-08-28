# ********************************************************************
# Name    : ENM MO
# Summary : Class used primarily by Cm Import.
#           Provides an ENM MO as a Python object, provides node,
#           netsim and FDN path information, which is used to
#           generate import files.
# ********************************************************************

from enmutils_int.lib.enm_user import get_workload_admin_user
from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils.lib import log


ONE_INSTANCE_VERIFICATION = "1 instance(s)"


class EnmMo(object):
    CREATE_CMD = 'cmedit create {fdn} {attrs}'
    DELETE_CMD = 'cmedit delete {fdn}'

    def __init__(self, name, mo_id, fdn, attrs=None, user=None, is_leaf=False):
        self.name = name
        self.mo_id = str(mo_id)
        self.fdn = fdn
        self.attrs = attrs or {}
        self.user = user
        self.is_leaf = is_leaf

    def __hash__(self):
        return hash(self.fdn)

    def __eq__(self, other):
        other_fdn = getattr(other, 'fdn', None) or other.get('fdn')
        return self.fdn == other_fdn

    def __str__(self):
        return '%s=%s' % (self.name, self.mo_id)

    def create(self):
        """
        Executes the create command

        :raises AssertionError: raised if the attributes are not available
        :raises ScriptEngineResponseValidationError: raised if the command failed to execute correctly
        """
        if not self.attrs:
            raise AssertionError('Attributes must be present in order to create the MO')
        user = self.user or get_workload_admin_user()
        cmd = self.CREATE_CMD.format(
            fdn=self.fdn,
            attrs='; '.join('{0}="{1}"'.format(
                att_name, att_val) for att_name, att_val in self.attrs.iteritems()))
        response = user.enm_execute(cmd)
        if not any(ONE_INSTANCE_VERIFICATION in line for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot create mo "%s". Response was "%s"' % (
                    self.fdn, ', '.join(response.get_output())), response=response)

    def delete(self):
        user = self.user or get_workload_admin_user()
        response = user.enm_execute(self.DELETE_CMD.format(fdn=self.fdn))
        if not any(ONE_INSTANCE_VERIFICATION in line for line in response.get_output()):
            raise ScriptEngineResponseValidationError(
                'Cannot delete subnetwork "%s". Response was "%s"' % (
                    self.name, ', '.join(response.get_output())), response=response)
        log.logger.debug('Successfully deleted mo "%s"' % self.fdn)


class MoAttrs(object):
    CMD = 'cmedit get {nodes} {mo_attrs}'

    def __init__(self, user, nodes, mos_attrs):
        """
        :param user: user object to make requests
        :type user: enmutils.lib.enm_user_2.User
        :param nodes: list of nodes to get the MOs of
        :type nodes: list
        :param mos_attrs: dict of mo names with their attrs in a list
        :type mos_attrs: dict
        """
        self.user = user
        self.nodes = nodes
        self.mos_attrs = mos_attrs

    def fetch(self):
        nodes_str = ';'.join(node.node_id for node in self.nodes)
        mos_str = ';'.join('{0}.({1})'.format(mo_name, ','.join(mo_attrs)) for mo_name, mo_attrs in self.mos_attrs.iteritems())
        response = self.user.enm_execute(self.CMD.format(nodes=nodes_str, mo_attrs=mos_str))
        return self._parse(response)

    def _parse(self, response):
        output = {}
        fdn = None
        response = [line for line in response.get_output() if line and 'instance(s)' not in line]
        if not response:
            raise ScriptEngineResponseValidationError('Cannot fetch the mos attrs %s' % str(self.mos_attrs), response=response)
        for line in response:
            if line.startswith('FDN'):
                fdn = line
                continue
            stripped_attr = [l.strip() for l in line.split(':', 1)]
            key, value = stripped_attr
            output.setdefault(fdn, {})[key] = value

        return output
