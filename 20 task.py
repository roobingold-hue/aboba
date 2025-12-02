import requests

def test_api_success():
    response = requests.get("https://35finance.mskobr.ru/")
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < 1.0