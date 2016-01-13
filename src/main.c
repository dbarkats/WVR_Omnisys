// ALMA WVR client example
#include <sys/types.h>
#include <sys/socket.h>
#include <stdio.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <getopt.h>

#define GET_INT_MBUF0			0x0110
#define GET_INT_MBUF1			0x0118
#define GET_INT_MBUF2			0x0120
#define GET_INT_MBUF3			0x0128

#define PART_ID					1396
#define PART_REV				0

#define MEASBUF_SIZE			128
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
void print_usage(void)
{
	printf("Simple test application for Omnisys ALMA WVR ");
	printf("(%4d-%02d, svn: %s)\n", PART_ID, PART_REV, PART_SVN);
	printf("Usage: [-hvb:i:]\n");
	printf(" -h --help          Displays this usage information\n");
	printf(" -v --verbose       Verbose output\n");
	printf(" -b --band NR       Select band [0..3]\n");
	printf(" -i --interval sec  Interval for continuous reading\n");
}
//---------------------------------------------------------------
int main(int argc, char *argv[])
{
	// Declaring variables and default settings
	int next;
	int sockfd;
	int i;
	struct sockaddr_in address;
	struct ethMsg msgWrite, msgRead;
	const char wvr_ip[] = "192.168.168.230";
	void *data_ptr;
	unsigned int bufCntr, bufSize;
	float bufTimestamp;
	float *float_ptr;
	int interval = -1;
	int ret;
	int verbose = 0;
	int band = 0;

	// This struct lists the valid long options
	const struct option long_options[] = {
		{ "help",		0, NULL, 'h' },
		{ "verbose",	0, NULL, 'v' },
		{ "band",		1, NULL, 'b' },
		{ "interval",	1, NULL, 'i' },
		{ NULL, 		0, NULL, 0 }
	};

	// Parse command line options
	do {
		next = getopt_long(argc,argv,"hvb:i:",long_options, NULL);
		switch(next) {
			case 'h' :
			case '?' :
				print_usage();
				exit(0);
			case 'v' :
				verbose++;
				break;
			case 'b' :
				band = atoi(optarg);
				break;
			case 'i' :
				interval = atoi(optarg);
				break;
			case -1 :
				break;
			default :
				abort();
		}
	} while (next != -1);

	if(interval > (int)(MEASBUF_SIZE/0.048)) {
		fprintf(stderr, "Interval should be lower than %d to prevent overflow\n", (int)(MEASBUF_SIZE/0.048));
		exit(0);
	}
	
	// Setup message
	switch(band) {
		case 0:
			msgWrite.address = GET_INT_MBUF0;
			break;
		case 1:
			msgWrite.address = GET_INT_MBUF1;
			break;
		case 2:
			msgWrite.address = GET_INT_MBUF2;
			break;
		case 3:
			msgWrite.address = GET_INT_MBUF3;
			break;
		default:
			fprintf(stderr, "Band %d out of range (0..3)\n", band);
			exit(0);
	}
	
	// Allocate memory for maximum sized data
	data_ptr = malloc(4*MEASBUF_SIZE*sizeof(unsigned int));

	do {
		// Create a socket for the client
		sockfd = socket(AF_INET, SOCK_STREAM, 0);
		address.sin_family = AF_INET;
		address.sin_addr.s_addr = inet_addr(wvr_ip);
		address.sin_port = htons(9734);

		// Connect our socket to the server's socket
		if(connect(sockfd, (struct sockaddr *)&address, sizeof(address)) == -1) {
			perror("oops: could not connect");
			goto cleanup;
		}
		
		// Send command and read response
		if(write(sockfd, &msgWrite, sizeof(msgWrite)) < 0)
			goto cleanup;
		if((ret = read(sockfd, &msgRead, sizeof(msgRead))) < 0)
			goto cleanup;
		
		// Response holds information on size of data and timestamp of last data
		float_ptr = (float*) &(msgRead.data[0]);
		bufCntr = (unsigned int) *float_ptr++;
		bufTimestamp = *float_ptr;
		bufSize = 4 * bufCntr * sizeof(unsigned int);
		if(bufCntr > 0) {
			ret = 0;
			while(bufSize > 0) {
				if((ret = read(sockfd, data_ptr + ret, bufSize)) < 0)
					goto cleanup;

				bufSize -= ret;
			}
		}
		
		// Print data
		if(verbose) {
			printf("Timestamp: %.3f s\n", bufTimestamp);
			printf("BufCntr: %d\n", bufCntr);
			printf("Returned message: %s\n", msgRead.msg);
			printf("timestamp\t cold\t skyA\t hot\t skyB\n");
		}

		bufTimestamp -= (bufCntr-1) * 0.048;
		for(i=0; i<bufCntr; i++) {
			printf("%.3f\t %d\t %d\t %d\t %d\n", bufTimestamp+(i*0.048),
				*((unsigned int*)data_ptr + 4*i + 0),
				*((unsigned int*)data_ptr + 4*i + 1),
				*((unsigned int*)data_ptr + 4*i + 2),
				*((unsigned int*)data_ptr + 4*i + 3));
		}
	
		// Close socket and sleep for a while before connecting again
		close(sockfd);
		if(interval > 0)
			sleep(interval);
		
	} while(interval >= 0);
	
cleanup:
	free(data_ptr);
	exit(0);
}
