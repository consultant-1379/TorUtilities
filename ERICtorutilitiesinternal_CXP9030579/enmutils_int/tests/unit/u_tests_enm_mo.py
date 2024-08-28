#!/usr/bin/env python
import unittest2
from testslib import unit_test_utils
from enmutils.lib.exceptions import ScriptEngineResponseValidationError
from enmutils_int.lib.enm_mo import EnmMo, MoAttrs

from mock import Mock


class EnmMoUnitTests(unittest2.TestCase):

    FDN = ("SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,ManagedElement=1,ENodeBFunction=1,"
           "EUtranCellFDD=LTE03ERBS00160-1,EUtranFreqRelation=4,EUtranCellRelation=7")

    def setUp(self):
        self.user = Mock()
        self.mo_1 = EnmMo("EUtranFreqRelation", '1', ("SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,"
                                                      "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00160-1"
                                                      ",EUtranFreqRelation=4,EUtranCellRelation=7"),
                          user=self.user, attrs={'foo': ['bar']})
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_mo_create__is_successful(self):
        response = Mock()
        response.get_output.return_value = ['1 instance(s) created']
        self.user.enm_execute.return_value = response
        self.mo_1.create()

    def test_mo_create__raises_assertion_error(self):
        self.mo_1.attrs = None
        self.assertRaises(AssertionError, self.mo_1.create)

    def test_mo_create__raises_scriptengineresponsevalidationerror(self):
        response = Mock()
        response.get_output.return_value = ['Mandatory attribute missing']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.mo_1.create)

    def test_mo_delete__is_successful(self):
        response = Mock()
        response.get_output.return_value = ['1 instance(s) deleted']
        self.user.enm_execute.return_value = response
        self.mo_1.delete()

    def test_mo_delete__raises_scriptengineresponsevalidationerror(self):
        response = Mock()
        response.get_output.return_value = ['Mandatory attribute missing']
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.mo_1.delete)

    def test__hash__is_successful(self):
        self.assertEqual(hash(self.FDN), self.mo_1.__hash__())

    def test__eq__is_successful(self):
        mo_2 = EnmMo("EUtranFreqRelation", '1',
                     ("SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,"
                      "ManagedElement=1,ENodeBFunction=1,EUtranCellFDD=LTE03ERBS00160-1"
                      ",EUtranFreqRelation=4,EUtranCellRelation=7"),
                     user=self.user, attrs={'foo': ['bar']})
        self.assertTrue(self.mo_1.__eq__(mo_2))

    def test__str__is_successful(self):
        self.assertEqual('EUtranFreqRelation=1', self.mo_1.__str__())


class MoAttrsUnitTests(unittest2.TestCase):

    def setUp(self):
        self.user = Mock()
        nodes = [Mock(node_id="ID")]
        self.mo_attrs = MoAttrs(user=self.user, nodes=nodes, mos_attrs={'EUtranCellRelation': ['isHoAllowed']})
        unit_test_utils.setup()

    def tearDown(self):
        unit_test_utils.tear_down()

    def test_mo_fetch_is_successful(self):
        response = Mock()
        fdn1 = ("FDN : SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,ManagedElement=1,ENodeBFunction=1,"
                "EUtranCellFDD=LTE03ERBS00160-1,EUtranFreqRelation=4,EUtranCellRelation=7")
        fdn2 = ("FDN : SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,ManagedElement=1,ENodeBFunction=1,"
                "EUtranCellFDD=LTE03ERBS00160-1,EUtranFreqRelation=4,EUtranCellRelation=8")
        response.get_output.return_value = [fdn1, "isHoAllowed:true", fdn2, "isHoAllowed:false", "2 instance(s)"]
        self.user.enm_execute.return_value = response
        res = self.mo_attrs.fetch()
        self.assertEqual(res, {fdn1: {'isHoAllowed': 'true'}, fdn2: {'isHoAllowed': 'false'}})

    def test_mo_fetch_successfully_splits_with_multiple_semi_colons_in_attrs(self):
        response = Mock()
        fdn1 = ("FDN : SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,ManagedElement=1,ENodeBFunction=1,"
                "EUtranCellFDD=LTE03ERBS00160-1,EUtranFreqRelation=4,EUtranCellRelation=Lrat:EUtranCellRelation")
        fdn2 = ("FDN : SubNetwork=ERBS-SUBNW-2,MeContext=netsim_LTE03ERBS00160,ManagedElement=1,ENodeBFunction=1,"
                "EUtranCellFDD=LTE03ERBS00160-1,EUtranFreqRelation=4,EUtranCellRelation=8")
        response.get_output.return_value = [fdn1, "EUtranCellRelation:Lrat:EUtranCellRelation", fdn2,
                                            "isHoAllowed:false", "2 instance(s)"]
        self.user.enm_execute.return_value = response
        res = self.mo_attrs.fetch()
        self.assertEqual(res, {fdn1: {'EUtranCellRelation': 'Lrat:EUtranCellRelation'},
                               fdn2: {'isHoAllowed': 'false'}})

    def test_mo_fetch_raises_script_engine_error_if_failed(self):
        response = Mock()
        response.get_output.return_value = ["2 instance(s)"]
        self.user.enm_execute.return_value = response
        self.assertRaises(ScriptEngineResponseValidationError, self.mo_attrs.fetch)


if __name__ == "__main__":
    unittest2.main(verbosity=2)
