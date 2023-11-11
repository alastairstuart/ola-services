Development dependencies

`
brew install protobuf
pip3 install "grpclib[protobuf]"
pip3 install grpcio-tools
`

Compile the hithchiker.proto protocol if changing it 

`python3 -m grpc_tools.protoc -I. --python_out=. --grpclib_python_out=. hitchhiker.proto`
