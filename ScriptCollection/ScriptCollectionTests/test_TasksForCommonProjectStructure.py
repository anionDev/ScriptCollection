import unittest
from ..ScriptCollection.TasksForCommonProjectStructure import TasksForCommonProjectStructure


class TasksForCommonProjectStructureTests(unittest.TestCase):

    def test_sort_codenits_1(self) -> None:
        # arrange
        t = TasksForCommonProjectStructure()
        function_input = {}
        expected_result = []

        # act
        actual_result = t._internal_sort_codenits(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_2(self) -> None:
        # arrange
        t = TasksForCommonProjectStructure()
        function_input = {
            'codeunit_01': {}
        }
        expected_result = ['codeunit_01']

        # act
        actual_result = t._internal_sort_codenits(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_3(self) -> None:
        # arrange
        t = TasksForCommonProjectStructure()
        function_input = {
            'codeunit_01': {},
            'codeunit_02': {'codeunit_01'}
        }
        expected_result = ['codeunit_01', 'codeunit_02']

        # act
        actual_result = t._internal_sort_codenits(function_input)

        # assert
        assert expected_result == actual_result

    def test_sort_codenits_4(self) -> None:
        # arrange
        t = TasksForCommonProjectStructure()
        function_input = {
            'codeunit_01': {},
            'codeunit_02': {'codeunit_03', 'codeunit_01'},
            'codeunit_04': {'codeunit_01'},
            'codeunit_03': {'codeunit_04'}
        }
        expected_result = ['codeunit_01', 'codeunit_04', 'codeunit_03', 'codeunit_02']

        # act
        actual_result = t._internal_sort_codenits(function_input)

        # assert
        assert expected_result == actual_result
