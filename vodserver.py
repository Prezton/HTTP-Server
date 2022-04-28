import sys
import socket
import os
import threading
import time
from datetime import datetime

port = 0
BUFSIZE = 1024
content_type_dict = {}
CHUNKSIZE = 5242880

class HTTPServer:
    def __init__(self, port):
        self.port = port
        self.s = None
        self.createSocket()
        # {uri: ["keep-alive" True /"close" False, 200/206]}
        self.conn = dict()

    def parse_request(self, req, connection):
        req = req.decode()
        tmp = req.split("\n")
        connFlag = True
        type = 200
        for line in tmp:
            tmpLine = line.split(":")
            if tmpLine[0] == "Connection":
                connStatus = tmpLine[1].strip()
                if connStatus == "close" or connStatus == "Close":
                    connFlag = False
            if tmpLine[0].strip() == "range" or tmpLine[0].strip() == "Range":
                type = 206

        uri = (tmp[0].split("HTTP")[0])[5:].strip()
        self.conn[uri] = [connFlag, type]

        if uri.startswith("confidential"):
            self.handle_forbidden(uri, connection)
            return
        # Terminate flag set by client

        fileName = os.path.join("content", uri)
        print(fileName)

        # if not connFlag:
        #     self.terminate(uri, fileName)

        if not os.path.exists(fileName):
            self.handle_not_found(uri, connection)
            return

        self.serve_request(fileName, uri, connection)



    def terminate(self, uri, fileName):
        pass

    def handle_not_found(self, uri, connection):
        response = self.get_404_response(uri)
        connection.send(response.encode())
        print("404 Not Found sent")

    def handle_forbidden(self, uri, connection):
        response = self.get_403_response(uri)
        connection.send(response.encode())
        print("403 Forbidden Sent")

    def get_403_response(self, uri):
        time_struct = time.localtime()
        current_time = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time_struct)
        time_header = "Date: " + str(current_time) + "\r\n"
        content_type_header = "Content-Type: " + "text/html\r\n"

        if not self.conn[uri][0]:
            conn_header = "Connection: close\r\n"
        else:
            conn_header = "Connection: keep-alive\r\n"
        payload = "<html>\n<head>\n<style type=text/css>\n\n</style>\n</head>\n\n<body><p>The URI you are requesting is forbidden\n<br><br> \nPermission Denied.</p>\n\n</body>\n</html>\n"
        content_length_header = "Content-Length: " + str(len(page)) + "\r\n"
        header = "HTTP/1.1 403 Forbidden\r\n" + time_header + content_type_header + content_length_header + conn_header + "\r\n"
        response = header + payload
        return response



    def serve_request(self, fileName, uri, connection):

        header = self.get_header(fileName, uri)
        response = header.encode() + self.get_payload(fileName)
        connection.send(response)
        print("response sent")

    def get_header(self, fileName, uri):
        type = self.conn[uri][1]

        # Get Date
        time_struct = time.localtime()
        current_time = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time_struct)
        time_header = "Date: " + str(current_time) + "\r\n"
        # print(time_header)

        # Get Last-Modified
        modTimesinceEpoc = os.path.getmtime(fileName)
        modificationTime = datetime.fromtimestamp(modTimesinceEpoc).strftime('%c')
        modificationTime = modificationTime[:3] + "," + modificationTime[3:11] + modificationTime[20:24]
        last_modified_header = "Last-Modified: " + modificationTime + "\r\n"
        # print(last_modified_header)

        # Get Accept-Ranges
        accept_range_header = "Accept-Ranges: bytes" + "\r\n"

        # Get Content-Length
        fileLength = os.path.getsize(fileName)
        if type == 200:
            content_length_header = "Content-Length: " + str(fileLength) + "\r\n"

        # Get Connection
        flag = "keep-alive"
        if not self.conn[uri][0]:
            flag = "close"
        conn_header = "Connection: " + flag + "\r\n"

        # Get content type
        content_type_header = "Content-Type: " + self.get_content_type(fileName)

        if type == 206:
            content_range_header = "Content-Range: " + self.get_range(fileName)

        if type == 200:
            header = "HTTP/1.1 200 OK\r\n"
        elif type == 206:
            header = "HTTP/1.1 206 Partial Content\r\n"
            # Get Content-Ranges
        etag_header = "ETag: " + "None\r\n"
        server_header = "Server: local host \r\n"
        header += time_header + last_modified_header + accept_range_header + content_length_header + conn_header + content_type_header + etag_header + server_header + "\r\n"

            # get range
        return header

    def get_range(self, fileName):
        pass

    def get_content_type(self, fileName):
        if fileName.endswith(".txt"):
            return "text/plain\r\n"
        if fileName.endswith(".css"):
            return "text/css\r\n"
        if fileName.endswith(".htm") or fileName.endswith(".html"):
            return "text/hyml\r\n"
        if fileName.endswith(".gif"):
            return "image/gif\r\n"
        if fileName.endswith(".jpg") or fileName.endswith(".jpeg"):
            return "image/jpeg\r\n"
        if fileName.endswith(".png"):
            return "image/png\r\n"
        if fileName.endswith(".mp4"):
            return "video/mp4\r\n"
        if fileName.endswith(".webm") or fileName.endswith(".ogg"):
            return "video/webm\r\n"
        if fileName.endswith(".js"):
            return "application/javascript\r\n"
        else:
            return "application/octet-stream\r\n"

    def get_payload(self, fileName, offset = 0, type = 200):
        file = open(fileName, "rb")
        if type == 206:
            file.seek(offset)
            chunk = file.read(CHUNKSIZE)
            return chunk
        data = file.read(CHUNKSIZE)
        return data

    def get_404_response(self, uri):
        time_struct = time.localtime()
        current_time = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time_struct)
        time_header = "Date: " + str(current_time) + "\r\n"
        content_type_header = "Content-Type: " + "text/html\r\n"

        if not self.conn[uri][0]:
            conn_header = "Connection: close\r\n"
        else:
            conn_header = "Connection: keep-alive\r\n"
        # page = "<html>\n" + "<head>\n" + "<style type=text/css>\n" + "</style>\n" + "</head>\n" + "<body>\n" + "<p>This was a web page for an organization that used to exist. This organization no longer exists as it has been replaced with a new organization to teach surf kids the values and love of the ocean. The new site is: https://www.pleasurepointsurfclub.com/\n" +"<br><br>\n" + "If you came upon this page by mistake, try checking the URL in your web browser.</p>\n" +"</body>\n" +"</html>"
        payload = "<html>\n<head>\n<style type=text/css>\n\n</style>\n</head>\n\n<body><p>The URI you are requesting does not exist\n<br><br> \nTry checking the URL in your web browser.</p>\n\n</body>\n</html>\n"
        content_length_header = "Content-Length: " + str(len(page)) + "\r\n"
        header = "HTTP/1.1 404 Not Found\r\n" + time_header + content_type_header + content_length_header + conn_header + "\r\n"
        response = header + payload
        return response

    def start(self):
        self.s.listen()
        # ACCEPT is a blocking call
        t = threading.Thread
        while True:
            conn, addr = self.s.accept()
            req = conn.recv(BUFSIZE)
            req_handle_thread = threading.Thread(target=self.parse_request, args=(req, conn, ))
            req_handle_thread.start()
            print("REQ is: \n", req.decode())






    def createSocket(self):
        # Create socket instance
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # localip = socket.gethostbyname(socket.gethostname())
        localip = "127.0.0.1"

        try:
            self.s.bind((localip, self.port))
        except socket.error as e:
            sys.exit(-1)


if __name__ == "__main__":
    port = int(sys.argv[1])
    # print(type(port))
    server = HTTPServer(port)
    server.start()
