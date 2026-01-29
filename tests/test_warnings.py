"""Integration tests for weather warnings functionality"""

# pylint: disable=redefined-outer-name

import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from meteo_lt import MeteoLtAPI


@pytest_asyncio.fixture
async def api_client():
    """Create API client for testing"""
    client = MeteoLtAPI()
    yield client
    # Cleanup: close the client after test completes
    await client.close()


@pytest.fixture
def mock_warnings_data():
    """Mock warnings JSON data"""
    return {
        "phenomenon_groups": [
            {
                "phenomenon_category": "wind",
                "area_groups": [
                    {
                        "areas": [{"id": "lt.lhms.county:LT002", "name": "Kauno apskritis"}],
                        "single_alerts": [
                            {
                                "phenomenon": "wind",
                                "severity": "Moderate",
                                "description": {
                                    "en": "Strong wind up to 20 m/s",
                                    "lt": "Stiprus vėjas iki 20 m/s",
                                },
                                "instruction": {
                                    "en": "Be careful",
                                    "lt": "Būkite atsargūs",
                                },
                                "t_from": "2025-09-30T12:00:00Z",
                                "t_to": "2025-09-30T18:00:00Z",
                            }
                        ],
                    }
                ],
            }
        ]
    }


@pytest.fixture
def mock_file_list():
    """Mock file list response"""
    return ["https://www.meteo.lt/meteo_jobs/pavojingi_met_reisk_ibl/20250930120000-00000001"]


@pytest.mark.asyncio
async def test_get_weather_warnings_success(api_client, mock_file_list, mock_warnings_data):
    """Test successful weather warnings retrieval"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        # Mock the file list response
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status.return_value = None

        # Mock the warnings data response
        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status.return_value = None

        # Configure the mock to return different responses for different calls
        mock_get.return_value.__aenter__.side_effect = [
            mock_list_response,
            mock_data_response,
        ]

        warnings = await api_client.get_weather_warnings()

        assert isinstance(warnings, list)
        assert len(warnings) == 1
        assert warnings[0].county == "Kauno apskritis"
        assert warnings[0].warning_type == "wind"
        assert warnings[0].severity == "Moderate"


@pytest.mark.asyncio
async def test_get_weather_warnings_for_specific_area(api_client, mock_file_list, mock_warnings_data):
    """Test weather warnings for specific administrative division"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_list_response = AsyncMock()
        mock_list_response.json.return_value = mock_file_list
        mock_list_response.raise_for_status.return_value = None

        mock_data_response = AsyncMock()
        mock_data_response.text.return_value = json.dumps(mock_warnings_data)
        mock_data_response.raise_for_status.return_value = None

        mock_get.return_value.__aenter__.side_effect = [
            mock_list_response,
            mock_data_response,
        ]

        warnings = await api_client.get_weather_warnings("Kauno miesto")

        assert isinstance(warnings, list)
        assert len(warnings) == 1  # Should match Kauno apskritis


@pytest.mark.asyncio
async def test_get_weather_warnings_empty_response(api_client):
    """Test handling of empty warnings response"""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value.__aenter__.return_value = mock_response

        warnings = await api_client.get_weather_warnings()

        assert isinstance(warnings, list)
        assert len(warnings) == 0
