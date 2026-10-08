import pytest
import requests

def test_api_en_linea():
    """
    Verifica que la API esté viva y que el mapa cargue correctamente (Código 200 OK)
    """
    try:
        respuesta = requests.get("http://localhost:8000/")
        assert respuesta.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("La API no está levantada o no se puede conectar.")