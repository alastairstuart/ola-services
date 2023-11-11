Development dependencies

`
brew install protobuf
pip3 install "grpclib[protobuf]"
pip3 install grpcio-tools
`

Compile the hithchiker.proto protocol if changing it 

`python3 -m grpc_tools.protoc -I. --python_out=. --grpclib_python_out=. hitchhiker.proto`


Test the functions

`

grpcurl -plaintext -proto hitchhiker.proto localhost:50051 hitchhiker.HitchhikerSource/GetSourceId

grpcurl -plaintext -proto hitchhiker.proto -d '{"clientId": "simulated-client", "destinationId": "befit_1"}' localhost:50051 hitchhiker.HitchhikerSource/GetDownloads

grpcurl -plaintext -proto hitchhiker.proto -d '{
  "clientId": "simulated-client",
  "files": [
    {
      "filename": "log-79b5c513422783f4-1699720554330.json"
    },
    {
      "filename": "log-79b5c513422783f4-1699720552417.json"
    }
  ]
}' localhost:50051 hitchhiker.HitchhikerSource/DownloadFile

grpcurl -plaintext -proto hitchhiker.proto -d '{
  "clientId": "simulated-client",
  "destinationId": "befit_1",
  "files": [
    {
      "filename": "log-79b5c513422783f4-1699720552417.json"
    }
  ]
}' localhost:50051 hitchhiker.HitchhikerSource/MarkDelivered

`