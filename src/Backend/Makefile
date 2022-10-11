main:main.cpp resolvePacket.o
	g++ main.cpp resolvePacket.o -o main -lmemif -luv -std=c++17 -I.
resolvePacket.o:resolvePacket.cpp
	g++ resolvePacket.cpp -o resolvePacket.o -I. -std=c++17
main_backup:main_backup.c icmp_proto.o
	gcc main_backup.c icmp_proto.o -o main_backup -lmemif -lpthread -I.
icmp_proto.o:icmp_proto.c
	gcc -c icmp_proto.c -I.
