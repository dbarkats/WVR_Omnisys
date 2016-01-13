// ALMA WVR client example
#include <sys/types.h>
#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>

#define GET_WVR_STATE			0x0010
#define SET_WVR_STATE			0x8010
#define SET_CHOP_VEL			0x8150


//---------------------------------------------------------------
struct ethMsg {
	unsigned char size;
	unsigned short address;
	unsigned char data[8];
	char server_ip[20];
	char filename[40];
	char msg[40];
};
//---------------------------------------------------------------
int sendCommandReadResponse(int sockfd, struct ethMsg *msg)
{
	if(write(sockfd, msg, sizeof(struct ethMsg)) < 0)
		return -1;
	if(read(sockfd, msg, sizeof(struct ethMsg)) < 0)
		return -2;
	
	printf("Returned message: %s\n", msg->msg);
	return 0;
}

//-----------------------------------------------------------

struct timeval tmval;
long start_sec,start_usec; 

// microsecond timer
// gives time stamp in seconds and microseconds
#define GETTIME(i,j) \
  (gettimeofday(&tmval,NULL),\
  i=tmval.tv_usec,\
  j=tmval.tv_sec)

void ptime_screen(void) {
long usec,sec;

GETTIME(usec,sec);
sec-=start_sec;
usec-=start_usec;
if(usec<0) usec+=1000000,sec--;
printf("time=%ld.%06ld ",sec,usec);
}

//---------------------------------------------------------------
int main(int argc, char *argv[])
{
        // Declaring variables and default settings
        int sockfd;
	int i;
	struct sockaddr_in address;
	struct ethMsg msg;
	const char wvr_ip[] = "192.168.168.230";

	// Create a socket for the client
	for(i=0; i<100; i++) {
	  printf("%d ",i);
	  ptime_screen();
	  sockfd = socket(AF_INET, SOCK_STREAM, 0);
	  address.sin_family = AF_INET;
	  address.sin_addr.s_addr = inet_addr(wvr_ip);
	  address.sin_port = htons(9734);
	
	  // Connect our socket to the server's socket
	  if(connect(sockfd, (struct sockaddr *)&address, sizeof(address)) == -1) {
	    perror("oops: could not connect");
	    return -1;
	  }

	  // read WVR_state
	  msg.address = GET_WVR_STATE;
	  sendCommandReadResponse(sockfd, &msg);
	  close(sockfd);
	}
	
	// Setup chopper to 5 Hz
	//msg.address = SET_CHOP_VEL;
	//msg.data[0] = 0x3; // 0x3 = 5 Hz chop rate
	//sendCommandReadResponse(sockfd, &msg);
	
	// Set WVR state to CONFIGURATION
	//msg.address = SET_WVR_STATE;
	//msg.data[0] = 0x2; // 0x2 = CONFIG mode
	//msg.data[1] = 0;
	//sendCommandReadResponse(sockfd, &msg);
	
	//close(sockfd);
	exit(0);
}
