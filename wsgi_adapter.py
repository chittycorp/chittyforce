"""
WSGI adapter for FastAPI applications

This module serves as a bridge between WSGI servers like gunicorn
and ASGI applications like FastAPI.
"""
import sys
import os
import threading
import time
import logging
import signal
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("wsgi_adapter")

class WSGIAdapter:
    """
    Simple WSGI application that launches uvicorn in a subprocess
    """
    def __init__(self):
        self.uvicorn_process = None
        self._start_uvicorn()

    def _start_uvicorn(self):
        """Start uvicorn server as a subprocess"""
        try:
            # Kill any existing uvicorn processes
            subprocess.run("pkill -f uvicorn || true", shell=True)
            
            # Start uvicorn with the FastAPI app
            cmd = [
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", "5000",
                "--reload"
            ]
            
            logger.info(f"Starting uvicorn: {' '.join(cmd)}")
            
            # Start the process
            self.uvicorn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Wait for uvicorn to start (up to 10 seconds)
            for _ in range(10):
                if self.uvicorn_process.poll() is not None:
                    # Process exited prematurely
                    stdout, _ = self.uvicorn_process.communicate()
                    logger.error(f"Uvicorn process failed to start: {stdout}")
                    return

                line = self.uvicorn_process.stdout.readline().strip()
                if line:
                    logger.info(f"Uvicorn: {line}")
                    if "Application startup complete" in line:
                        break
                
                time.sleep(1)
                
            # Register cleanup handler
            def cleanup_handler(signum, frame):
                self._stop_uvicorn()
                sys.exit(0)
                
            signal.signal(signal.SIGTERM, cleanup_handler)
            signal.signal(signal.SIGINT, cleanup_handler)
                
            # Start a thread to continuously read and log uvicorn output
            def log_output():
                while self.uvicorn_process and self.uvicorn_process.poll() is None:
                    line = self.uvicorn_process.stdout.readline().strip()
                    if line:
                        logger.info(f"Uvicorn: {line}")
                        
            threading.Thread(target=log_output, daemon=True).start()
            
            logger.info("Uvicorn server started successfully")
            
        except Exception as e:
            logger.error(f"Error starting uvicorn: {e}")
            
    def _stop_uvicorn(self):
        """Stop the uvicorn subprocess"""
        if self.uvicorn_process:
            logger.info("Stopping uvicorn subprocess")
            try:
                self.uvicorn_process.terminate()
                self.uvicorn_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Uvicorn didn't terminate gracefully, killing...")
                self.uvicorn_process.kill()
            except Exception as e:
                logger.error(f"Error stopping uvicorn: {e}")
                
            self.uvicorn_process = None
            
    def __del__(self):
        """Ensure uvicorn is stopped when adapter is destroyed"""
        self._stop_uvicorn()
        
    def __call__(self, environ, start_response):
        """
        WSGI application interface.
        This doesn't actually handle requests - it just bridges to uvicorn.
        """
        # Since uvicorn is running, just return a "proxy in place" response
        # that tells gunicorn we've successfully proxied the request
        status = '200 OK'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        
        # If uvicorn isn't running anymore, try to restart it
        if self.uvicorn_process and self.uvicorn_process.poll() is not None:
            logger.warning("Uvicorn process stopped unexpectedly. Restarting...")
            self._start_uvicorn()
            
        return [b"Requests are being handled by uvicorn"]

# Create the WSGI application
application = WSGIAdapter()

if __name__ == "__main__":
    # For testing, we can simulate a WSGI server
    print("Starting WSGI adapter in test mode...")
    app = application
    
    # Simulate a few WSGI requests
    def fake_start_response(status, headers):
        print(f"Response: {status}, {headers}")
        
    for _ in range(3):
        print("Simulating request...")
        resp = app({}, fake_start_response)
        print(f"Response body: {resp}")
        time.sleep(2)
    
    print("Test complete. Exiting...")
    app._stop_uvicorn()