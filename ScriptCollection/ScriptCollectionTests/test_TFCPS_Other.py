import unittest
from ..ScriptCollection.ScriptCollectionCore import ScriptCollectionCore
from ..ScriptCollection.TFCPS.TFCPS_Tools_General import TFCPS_Tools_General


class TasksForCommonProjectStructureTests(unittest.TestCase):

    def test_sort_codenits_1(self) -> None:
        # arrange
        t = TFCPS_Tools_General(ScriptCollectionCore())
        function_input = {}
        expected_result = []

        # act
        actual_result = t._internal_get_sorted_codeunits_by_dict(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_2(self) -> None:
        # arrange
        t = TFCPS_Tools_General(ScriptCollectionCore())
        function_input = {
            'codeunit_01': {}
        }
        expected_result = ['codeunit_01']

        # act
        actual_result = t._internal_get_sorted_codeunits_by_dict(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_3(self) -> None:
        # arrange
        t = TFCPS_Tools_General(ScriptCollectionCore())
        function_input = {
            'codeunit_01': {},
            'codeunit_02': {'codeunit_01'}
        }
        expected_result = ['codeunit_01', 'codeunit_02']

        # act
        actual_result = t._internal_get_sorted_codeunits_by_dict(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_4(self) -> None:
        # arrange
        t = TFCPS_Tools_General(ScriptCollectionCore())
        function_input = {
            'codeunit_01': {},
            'codeunit_02': {'codeunit_03', 'codeunit_01'},
            'codeunit_04': {'codeunit_01'},
            'codeunit_03': {'codeunit_04'}
        }
        expected_result = ['codeunit_01', 'codeunit_04', 'codeunit_03', 'codeunit_02']

        # act
        actual_result = t._internal_get_sorted_codeunits_by_dict(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_reference_folder(self) -> None:
        assert TFCPS_Tools_General.sort_reference_folder("/folder/Latest", "/folder/Latest") == 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v1.1.1", "/folder/Latest") > 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/Latest", "/folder/v1.1.1") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.5.7", "/folder/v4.6.8") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v4.6.8", "/folder/v3.5.7") > 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.3.4") > 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.3.5") == 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.3.6") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.3.17") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.8.0") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.3.5", "/folder/v3.3.05") == 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v3.0.0", "/folder/v4.0.0") < 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v4.0.0", "/folder/v3.0.0") > 0
        assert TFCPS_Tools_General.sort_reference_folder("/folder/v4.0.0", "/folder/v4.0.0") == 0
