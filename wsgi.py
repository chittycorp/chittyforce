"""
WSGI adapter for FastAPI to work with gunicorn
"""
import sys
import os
from fastapi.applications import FastAPI
from main import app as fastapi_app

class WSGIMiddleware:
    """
    WSGI middleware for FastAPI to work with gunicorn.
    """
    def __init__(self, app: FastAPI):
        self.app = app

    def __call__(self, environ, start_response):
        """
        WSGI interface
        """
        path = environ.get('PATH_INFO', '')
        method = environ.get('REQUEST_METHOD', 'GET').upper()
        
        # Add query string if present
        if environ.get('QUERY_STRING'):
            path = path + '?' + environ.get('QUERY_STRING')

        # Create scope for ASGI
        scope = {
            'type': 'http',
            'asgi': {
                'version': '3.0',
                'spec_version': '2.0'
            },
            'http_version': environ.get('SERVER_PROTOCOL', 'HTTP/1.1').split('/')[1],
            'method': method,
            'scheme': environ.get('wsgi.url_scheme', 'http'),
            'path': path,
            'raw_path': path.encode(),
            'query_string': environ.get('QUERY_STRING', '').encode(),
            'root_path': environ.get('SCRIPT_NAME', ''),
            'headers': [(k.decode('latin1'), v.decode('latin1')) 
                        for k, v in self._get_headers(environ)],
            'client': self._get_client(environ),
            'server': self._get_server(environ),
        }

        # Create response arrays
        status_headers = []
        response_body = []
        
        def send_response(message_type, message):
            if message_type == 'http.response.start':
                status_headers.append((message['status'], message.get('headers', [])))
            elif message_type == 'http.response.body':
                response_body.append(message.get('body', b''))

        # Call the ASGI application
        def send(message_type, message):
            send_response(message_type, message)
            return None

        # Call the FastAPI application
        try:
            self.app(scope, lambda: None, send)  # This is a simplified version
            
            # Get status and headers from the response
            status_code, headers = status_headers[0] if status_headers else (200, [])
            
            # Start the WSGI response
            start_response(f"{status_code} {self._get_status_text(status_code)}", headers)
            
            # Return the response body
            return response_body
        except Exception as e:
            # Handle exceptions
            error_msg = f"Error processing request: {str(e)}"
            start_response('500 Internal Server Error', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(error_msg)))
            ])
            return [error_msg.encode()]
    
    @staticmethod
    def _get_headers(environ):
        """Get headers from WSGI environ"""
        headers = []
        for k, v in environ.items():
            if k.startswith('HTTP_'):
                header_name = k[5:].replace('_', '-').lower()
                headers.append((header_name.encode('latin1'), str(v).encode('latin1')))
        if environ.get('CONTENT_TYPE'):
            headers.append((b'content-type', environ['CONTENT_TYPE'].encode('latin1')))
        if environ.get('CONTENT_LENGTH'):
            headers.append((b'content-length', environ['CONTENT_LENGTH'].encode('latin1')))
        return headers
    
    @staticmethod
    def _get_client(environ):
        """Get client address from WSGI environ"""
        client_addr = environ.get('REMOTE_ADDR', '').strip()
        if not client_addr:
            return None
        client_port = environ.get('REMOTE_PORT')
        if client_port:
            return (client_addr, int(client_port))
        return None
    
    @staticmethod
    def _get_server(environ):
        """Get server address from WSGI environ"""
        server_addr = environ.get('SERVER_NAME', '').strip()
        if not server_addr:
            return None
        server_port = environ.get('SERVER_PORT')
        if server_port:
            return (server_addr, int(server_port))
        return None
    
    @staticmethod
    def _get_status_text(status_code):
        """Get status text from status code"""
        status_texts = {
            200: 'OK',
            201: 'Created',
            202: 'Accepted',
            204: 'No Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            409: 'Conflict',
            500: 'Internal Server Error',
        }
        return status_texts.get(status_code, 'Unknown')

# Create WSGI application
application = WSGIMiddleware(fastapi_app)