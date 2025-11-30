.PHONY: client server analysis


client:
	cd client && python main.py

server:
	cd server && python main.py

analysis:
	cd analysis && python main.py


gen_code_client:
	mkdir -p ./client/generated && python -m grpc_tools.protoc -I./_protos --python_out=./client/generated --grpc_python_out=./client/generated monitor.proto

gen_code_server:
	mkdir -p ./server/generated && python -m grpc_tools.protoc -I./_protos --python_out=./server/generated --grpc_python_out=./server/generated monitor.proto
gen_code:
	make gen_code_client && make gen_code_server

