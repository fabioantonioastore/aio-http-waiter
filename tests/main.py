import pytest
from aioresponses import aioresponses
from http_waiter import Client


@pytest.mark.asyncio
async def test_get_request_success():
    base_url = "https://api.exemplo.com"
    client = Client(base_url=base_url)

    with aioresponses() as m:
        m.get(f"{base_url}/data", status=200, payload={"status": "ok"})

        async with client:
            response = await client.get("/data")
            data = await response.json()

            assert response.status == 200
            assert data == {"status": "ok"}


@pytest.mark.asyncio
async def test_base_url_property():
    url = "https://api.teste.com"
    client = Client(base_url=url)
    assert client.base_url == url


@pytest.mark.asyncio
async def test_retry_logic_on_500_error():
    base_url = "https://api.retry.com"
    client = Client(base_url=base_url, attempts=2)

    with aioresponses() as m:
        m.get(f"{base_url}/retry", status=500)
        m.get(f"{base_url}/retry", status=200, payload={"status": "recovered"})

        async with client:
            response = await client.get("/retry")
            data = await response.json()

            assert response.status == 200
            assert data == {"status": "recovered"}


@pytest.mark.asyncio
async def test_session_closure():
    client = Client(base_url="https://api.fechar.com")

    async with client:
        session = await client._get_session()
        assert not session.closed

    assert session.closed


@pytest.mark.asyncio
async def test_multiple_methods():
    base_url = "https://api.methods.com"
    client = Client(base_url=base_url)

    with aioresponses() as m:
        m.post(f"{base_url}/post", status=201)
        m.delete(f"{base_url}/delete", status=204)

        async with client:
            res_post = await client.post("/post", json={"id": 1})
            res_del = await client.delete("/delete")

            assert res_post.status == 201
            assert res_del.status == 204
