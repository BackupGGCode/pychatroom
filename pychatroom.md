# Overview #

The program is implemented in Python programming language with Server-Client architecture. The default communication is group communication, which means the messages sent by every client is multicasted to every other clients. If one client want to chat with another client, it just needs to specify the client name in the message.

# Features #

  * Server-Client Architecture;
  * TCP Protocol
  * Multi-Threaded server, each thread is responsible for a client connection;
  * Multi-Threaded client, one for send message, another one for listening to server messages;
  * Mutex is used on server to exclusively operate on client sockets;
  * Special commands: "l" - list online users; "username>>>'message'" - send message to specific client;
  * When one client connects to/disconnect from the server, all other clients are notified;
  * GUI enabled;
  * cross-platform.