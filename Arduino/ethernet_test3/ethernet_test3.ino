// import Socket as S
//s = S.Socket(S.socket.AF_INET, S.socket.SOCK_STREAM)
// s.connect(('131.142.156.77',4321))
// while(1):
//    s.send('p')
//   print s.readline()
//    t0 = t1
//    t1 = time.time()
//    print t1-t0
//    dt.append(t1-t0)

#include <Ethernet2.h>

// Define Ethernet shield settings
const int port = 4321;
//byte ip[] = {131,142,156,77};
byte ip[] = {192,168,168,233};

byte mac[] = {0x90, 0xA2, 0xDA, 0x10, 0xDD, 0xCD};
EthernetServer server = EthernetServer(port);

void setup()
{
  // initialize the ethernet device
  Ethernet.begin(mac, ip);
  // start listening for clients
  server.begin();
}

void loop()
{
  // if an incoming client connects, there will be bytes available to read:
   EthernetClient client = server.available();
   client.setTimeout(0);
  if (client) {
 
    // read bytes from the incoming client and write them back
    // to any clients connected to the server:
    String Input  = client.readString();
    String whichMotor = Input.substring(0,1);
    server.print(whichMotor);
    int xpos = Input.substring(1).toInt();
    if  (xpos == 1000 ) {
     server.println("position 1000") ;
    } else {
     server.println(xpos) ;
    }
  }
}
