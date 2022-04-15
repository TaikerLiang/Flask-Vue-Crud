import os
from unittest.mock import Mock

from src.crawler.core.pipelines import BaseItemPipeline


class TestBaseItemPipeline:
    def test_init(self):
        # arrange
        expected_suffix = "suffix"
        expected_user = "user"
        expected_token = "token"
        expected_url = "https://api.example.com/"
        os.environ["EDI_ENGINE_USER"] = expected_user
        os.environ["EDI_ENGINE_TOKEN"] = expected_token
        os.environ["EDI_ENGINE_BASE_URL"] = expected_url

        # action
        pipeline = BaseItemPipeline(expected_suffix)

        # assert
        assert pipeline._edi_client.url == f"{expected_url}{expected_suffix}"
        assert pipeline._edi_client.edi_user == expected_user
        assert pipeline._edi_client.edi_token == expected_token

    def test_handle_err_result(self):
        # arrange
        pipeline = BaseItemPipeline("")
        mock_send_provider_result_to_edi_client = Mock()
        pipeline.send_provider_result_to_edi_client = mock_send_provider_result_to_edi_client
        expected_taskid = 123
        expected_result = {}

        mock_collector = Mock()
        mock_collector.is_default = Mock(return_value=True)

        # action
        pipeline.handle_err_result(mock_collector, expected_taskid, expected_result)

        # assert
        mock_collector.is_default.assert_called_once()
        mock_send_provider_result_to_edi_client.assert_called_once_with(task_id=expected_taskid, result=expected_result)

        # arrange
        mock_collector.is_default = Mock(return_value=False)
        mock_collector.build_final_data = Mock(return_value=expected_result)
        mock_send_provider_result_to_edi_client.reset_mock()

        # action
        pipeline.handle_err_result(mock_collector, expected_taskid, expected_result)

        # assert
        mock_collector.is_default.assert_called_once()
        mock_collector.build_final_data.assert_called_once()
        mock_send_provider_result_to_edi_client.assert_called_once_with(task_id=expected_taskid, result=expected_result)
