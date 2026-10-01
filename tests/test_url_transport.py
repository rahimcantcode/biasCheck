import socket
from unittest.mock import MagicMock, patch
import pytest
from backend.utils import PublicConnection, fetch_article_text


def test_transport_connects_to_checked_address_without_new_dns():
    address = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))
    sock = MagicMock()
    with patch('backend.utils.socket.socket', return_value=sock), patch('backend.utils.socket.getaddrinfo') as dns:
        connection = PublicConnection('example.com', 80, address, False, 10)
        connection.connect()
        sock.connect.assert_called_once_with(('93.184.216.34', 80))
        dns.assert_not_called()


def test_https_validates_requested_hostname():
    address = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))
    sock = MagicMock()
    with patch('backend.utils.socket.socket', return_value=sock), patch('backend.utils.ssl.create_default_context') as context:
        PublicConnection('example.com', 443, address, True, 10).connect()
        context.return_value.wrap_socket.assert_called_once_with(sock, server_hostname='example.com')


def test_redirect_to_private_network_rejected():
    public = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80))
    private = (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))
    with patch('backend.utils.socket.getaddrinfo', side_effect=[[public], [private]]), patch('backend.utils.PublicConnection') as conn:
        response = conn.return_value.getresponse.return_value
        response.status = 302
        response.getheader.return_value = 'http://localhost/private'
        with pytest.raises(ValueError, match='public'):
            fetch_article_text('http://example.com/article')
        assert conn.call_count == 1
        conn.return_value.close.assert_called_once()
