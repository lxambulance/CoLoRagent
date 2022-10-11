main:main.cpp icmp_proto.o
	g++ main.cpp icmp_proto.o -o main -lmemif -luv -std=c++17 -I.
main_backup:main_backup.c icmp_proto.o
	gcc main_backup.c icmp_proto.o -o main_backup -lmemif -lpthread -I.
icmp_proto.o:icmp_proto.c
	gcc -c icmp_proto.c -I.
