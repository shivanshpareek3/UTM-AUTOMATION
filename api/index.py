from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Deployment Successful. Note: Streamlit apps require a constantly running server and websockets, which Vercel Serverless Functions do not support. Please deploy your Streamlit app on Streamlit Community Cloud (share.streamlit.io) or Render.'.encode('utf-8'))
        return
