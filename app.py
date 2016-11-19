# -*- coding: utf-8 -*-
import time
import sqlite3
import argparse
import random
import os

import cherrypy

from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
from ws4py.websocket import WebSocket
from ws4py.messaging import TextMessage

from telegram import Bot, Update
from telegram.ext import Updater

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
USERS = ['mike', 'stella', 'john']

DB_STRING = 'data.db'

class ChatPlugin(WebSocketPlugin):
    def __init__(self, bus):
        WebSocketPlugin.__init__(self, bus)
        self.clients = {}

    def start(self):
        WebSocketPlugin.start(self)
        self.bus.subscribe('add-client', self.add_client)
        self.bus.subscribe('get-client', self.get_client)
        self.bus.subscribe('del-client', self.del_client)

    def stop(self):
        WebSocketPlugin.stop(self)
        self.bus.unsubscribe('add-client', self.add_client)
        self.bus.unsubscribe('get-client', self.get_client)
        self.bus.unsubscribe('del-client', self.del_client)

    def add_client(self, name, websocket):
        self.clients[name] = websocket

    def get_client(self, name):
        return self.clients[name]

    def del_client(self, name):
        del self.clients[name]

class ChatWebSocketHandler(WebSocket):
    def opened(self):
        cherrypy.engine.publish('add-client', self.username, self)

    def received_message(self, m):
        updater = Updater(cherrypy.config['app.tgtoken'])
        updater.bot.sendMessage(cherrypy.config['app.tgchat'], text=str(m))
        updater.stop()

    def closed(self, code, reason="A client left the room without a proper explanation."):
        cherrypy.engine.publish('del-client', self.username)
        cherrypy.engine.publish('websocket-broadcast', TextMessage(reason))

class Root(object):
    def __init__(self, host, port, ssl=False, ssl_port=9443):
        self.host = host
        self.port = port
        self.ssl_port = ssl_port
        self.ssl = ssl
        self.scheme = 'wss' if ssl else 'ws'

    @cherrypy.expose
    def index(self):
        return """<html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
      <style>
      #username {
        width: 100%;
        font-size: 1.2em;
        line-height: 3em;
      }
      </style>
    </head>
    <body>
    <h1>Web2Gram Engage</h1>
    <form action='/chatroom' id='chatform' method='get'>
      <input type='text' name='username' id='username' class='form-control'/><br />
      <input id='send' type='submit' value='Set Nickname' class='form-control btn btn-primary'/>
      </form>
    </body>
    </html>
    """

    @cherrypy.expose
    def chatroom(self, username=None):
        username = username or "User%d" % random.randint(0, 100)
        messages = ["Welcome ..."]

        return """<html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
      <style>
      textarea {
        -webkit-box-sizing: border-box;
        -moz-box-sizing: border-box;
        box-sizing: border-box;
        font-size: 1.2em;
        width: 100%%;
        max-height: 500em;
        overflow: auto;
      }
      #message {
        width: 100%%;
        font-size: 1.2em;
        line-height: 3em;
      }
      </style>
      <script   src="https://code.jquery.com/jquery-1.12.4.min.js"   integrity="sha256-ZosEbRLbNQzLpnKIkEdrPv7lOy9C27hHQ+Xp8a4MxAQ="   crossorigin="anonymous"></script>
      <script type='application/javascript'>
        $(document).ready(function() {

          websocket = '%(scheme)s://%(host)s:%(port)s/ws?username=%(username)s';
          if (window.WebSocket) {
            ws = new WebSocket(websocket, ['mytest']);
          }
          else if (window.MozWebSocket) {
            ws = MozWebSocket(websocket);
          }
          else {
            console.log('WebSocket Not Supported');
            return;
          }

          window.onbeforeunload = function(e) {
            $('#chat').val($('#chat').val() + 'Bye bye...\\n');
            ws.close(1000, '%(username)s left the room');

            if(!e) e = window.event;
            e.stopPropagation();
            e.preventDefault();
          };
          ws.onmessage = function (evt) {
             $('#chat').val($('#chat').val() + evt.data + '\\n');
             var textarea = document.getElementById('chat');
             textarea.scrollTop = textarea.scrollHeight;
          };
          ws.onopen = function() {
             ws.send("%(username)s entered the room");
          };
          ws.onclose = function(evt) {
             $('#chat').val($('#chat').val() + 'Connection closed by server: ' + evt.code + ' \"' + evt.reason + '\". Refresh to reconnect.\\n');
          };

          $('#send').click(function() {
             console.log($('#message').val());
             ws.send('%(username)s: ' + $('#message').val());
             $('#message').val("");
             return false;
          });
          var textarea = document.getElementById('chat');
          textarea.scrollTop = textarea.scrollHeight;
        });
      </script>
    </head>
    <body>
    <h1>Web2Gram Engage</h1>
    <form action='#' id='chatform' method='get'>
      <textarea id='chat' cols='35' rows='10'>%(messages)s</textarea>
      <br />
      <input type='text' id='message' placeholder='Type your message here. Be nice.' />
      <input id='send' type='submit' value='Send' class='form-control btn btn-primary'/>
      </form>
    </body>
    </html>
    """ % {'username': username, 'host': self.host,
           'port': self.ssl_port if self.ssl else self.port, 'scheme': self.scheme,
           'messages': "\n".join(messages) + "\n"}

    @cherrypy.expose
    def ws(self, username):
        # let's track the username we chose
        cherrypy.request.ws_handler.username = username
        cherrypy.log("Handler created: %s" % repr(cherrypy.request.ws_handler))

    @cherrypy.tools.json_in()
    @cherrypy.expose
    def webhook(self):
        print cherrypy.request.json
        bot = Bot(cherrypy.config['app.tgtoken'])
        update = Update.de_json(cherrypy.request.json, bot)
        username, message = update.message.text.split(':')
        client = cherrypy.engine.publish('get-client', username).pop()
        if username:
            cherrypy.log("Sent to:%s" % username)
            client.send("Operator: %s" % message)

if __name__ == '__main__':
    import logging
    import cherrypy_jinja2
    from ws4py import configure_logger
    configure_logger(level=logging.DEBUG)

    cj = cherrypy_jinja2.CherrypyJinja(os.path.join(PROJECT_ROOT, 'templates'))
    cj.setup()

    parser = argparse.ArgumentParser(description='Web2Gram')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', default=9000, type=int)
    parser.add_argument('--ssl-port', default=9443, type=int)
    parser.add_argument('--ssl', action='store_true')
    parser.add_argument('--cert', default='./server.crt', type=str)
    parser.add_argument('--key', default='./server.key', type=str)
    parser.add_argument('--chain', default='./server.chain', type=str)
    parser.add_argument('--tgtoken', type=str)
    parser.add_argument('--tgchat', type=str)
    args = parser.parse_args()

    cherrypy.config.update({
        'server.socket_host': args.host,
        'server.socket_port': args.port,
        'tools.staticdir.root': os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')),
        'app.tgtoken': args.tgtoken,
        'app.tgchat': args.tgchat,
    })
    config = {
        '/ws': {
            'tools.websocket.on': True,
            'tools.websocket.handler_cls': ChatWebSocketHandler,
            'tools.websocket.protocols': ['toto', 'mytest', 'hithere']
        },
        '/static': {
              'tools.staticdir.on': True,
              'tools.staticdir.dir': ''
        },
    }

    if args.ssl:
        ssl_server = cherrypy._cpserver.Server()
        ssl_server.socket_host = args.host
        ssl_server.ssl_certificate = args.cert
        ssl_server.ssl_private_key = args.key
        ssl_server.socket_port = args.ssl_port
        ssl_server.ssl_certificate_chain = args.chain
        ssl_server.subscribe()

    ChatPlugin(cherrypy.engine).subscribe()
    cherrypy.tools.websocket = WebSocketTool()

    app_root = Root(args.host, args.port, args.ssl, ssl_port=args.ssl_port)
    cherrypy.quickstart(app_root, '', config=config)
