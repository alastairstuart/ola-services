# Open Learning Architecture Services

This repository contains two services that are part of the Open Learning Architecture.

* metrics_local - recieves analytics logs from client devices and caches them.
* hitchhiker_source - a gRPC service for sharing the cached updates from metrics local with upstream ETL services.

These can be run either in a local dev environment or on an OpenWRT device/virtual machine.

## Set up on an OpenWRT VM

On a fresh OpenWRT VM running on 10.0.2.2, install some prerequisites:

```
opkg install curl
opkg install openssh-sftp-server # optional if you have another way of uploading the services
opkg install python3
opkg install python3-pip

scp ola-services root@10.0.2.2:~ # from your host, not in the VM

cd /root
cd ola-services/metrics_local
pip install -r requirements.txt

cd /root/ola-services/hitchhiker_source
pip install -r requirements.txt
```

## Demoing

On OpenWRT (or your local dev machine), first we start the services in seperate terminals

```
cd metrics_local
python3 metrics_local.py --data-root ../data

cd ../hitchhiker_source
python3 hitchhiker_source.py --data-root ../data
```


Then, on our host machine we can start sending data to metrics local (use 127.0.0.1 if not running on an OpenWRT VM)

```
cd metrics_local
for i in {1..5}; do ./simulateClient.sh http://10.0.2.2:8080; done
```

Alternatively, you could run actual clients pointing at the same URL. Unfortunately the provided metrics_local/countly_test.apk requires all network connectivity to be over HTTPs with a signed certificate.


We can then test the gRPC service's functions e.g. using grpcurl, again from the host machine

```
$ brew install grpcurl

$ cd hitchhiker_source
$ grpcurl -plaintext -proto hitchhiker.proto 10.0.2.2:50051 hitchhiker.HitchhikerSource/GetSourceId
{
  "id": "pilot04"
}

$ grpcurl -plaintext -proto hitchhiker.proto -d '{"clientId": "simulated-client", "destinationId": "befit_1"}' 10.0.2.2:50051 hitchhiker.HitchhikerSource/GetDownloads
{
  "files": [
    {
      "fileid": "7781121272f163bac8d789918c51e39b",
      "filename": "log-79b5c513422783f4-1699790659797.json",
      "type": "application/json"
    },
    {
      "fileid": "71303001d3158fd8deb98f57b9a6e4a6",
      "filename": "log-79b5c513422783f4-1699790659843.json",
      "type": "application/json"
    },
    {
      "fileid": "f4b77cd70c3abf94c9d8569207d728ba",
      "filename": "log-79b5c513422783f4-1699790659880.json",
      "type": "application/json"
    },
    {
      "fileid": "dc7c321f1aa014cb0fdb8f0a667ef0c6",
      "filename": "log-79b5c513422783f4-1699790659916.json",
      "type": "application/json"
    },
    {
      "fileid": "66d461ad967f03ffc7d20096d0381acb",
      "filename": "log-79b5c513422783f4-1699790659951.json",
      "type": "application/json"
    }
  ]
}

$ grpcurl -plaintext -proto hitchhiker.proto -d '{
  "clientId": "simulated-client",
  "files": [
    {
      "filename": "log-79b5c513422783f4-1699790659797.json"
    },
    {
      "filename": "log-79b5c513422783f4-1699790659843.json"
    }
  ]
}' 10.0.2.2:50051 hitchhiker.HitchhikerSource/DownloadFile
{
  "fileid": "7781121272f163bac8d789918c51e39b",
  "filename": "log-79b5c513422783f4-1699790659797.json",
  "type": "application/json",
  "blob": "eyJhcHBfa2V5IjogImFlZTMzZjE5N2Y3M2JjNWY3Y2E5OTI2MWE2ZjI1M2NhYTJkNGY2MTQiLCAidGltZXN0YW1wIjogIjE2OTk3OTA2NTk3OTciLCAiaG91ciI6ICIxMiIsICJkb3ciOiAiNyIsICJ0eiI6ICIwIiwgInNka192ZXJzaW9uIjogIjIwLjA0IiwgInNka19uYW1lIjogImphdmEtbmF0aXZlLWFuZHJvaWQiLCAidXNlcl9kZXRhaWxzIjogIntcImN1c3RvbVwiOntcImRldmljZV9pZFwiOlwiQ1E4RFwiLFwib3RhXCI6XCIxXCJ9fSIsICJkZXZpY2VfaWQiOiAiNzliNWM1MTM0MjI3ODNmNCIsICJjaGVja3N1bSI6ICI3YzhlMGYxZWJmZGQ0ZDkxNjRhYzlmNTNhZTJmMjQzZDlkZTZhOWRjIn0="
}
{
  "fileid": "71303001d3158fd8deb98f57b9a6e4a6",
  "filename": "log-79b5c513422783f4-1699790659843.json",
  "type": "application/json",
  "blob": "eyJhcHBfa2V5IjogImFlZTMzZjE5N2Y3M2JjNWY3Y2E5OTI2MWE2ZjI1M2NhYTJkNGY2MTQiLCAidGltZXN0YW1wIjogIjE2OTk3OTA2NTk4NDMiLCAiaG91ciI6ICIxMiIsICJkb3ciOiAiNyIsICJ0eiI6ICIwIiwgInNka192ZXJzaW9uIjogIjIwLjA0IiwgInNka19uYW1lIjogImphdmEtbmF0aXZlLWFuZHJvaWQiLCAidXNlcl9kZXRhaWxzIjogIntcImN1c3RvbVwiOntcImRldmljZV9pZFwiOlwiQ1E4RFwiLFwib3RhXCI6XCIxXCJ9fSIsICJkZXZpY2VfaWQiOiAiNzliNWM1MTM0MjI3ODNmNCIsICJjaGVja3N1bSI6ICI3YzhlMGYxZWJmZGQ0ZDkxNjRhYzlmNTNhZTJmMjQzZDlkZTZhOWRjIn0="
}

$ grpcurl -plaintext -proto hitchhiker.proto -d '{
  "clientId": "simulated-client",
  "destinationId": "befit_1",
  "files": [
    {
      "filename": "log-79b5c513422783f4-1699720554330.json"
    },
    {
      "filename": "log-79b5c513422783f4-1699720552417.json"
    }
  ]
}' 10.0.2.2:50051 hitchhiker.HitchhikerSource/MarkDelivered
{}
```

## Running Unit Tests

Both services are unit tested with PyTest. To run them, in both services, install the developer requirements and run pytest:

```
pip install -r requirements_dev.txt
pytest
```

## Changing the gRPC protocol

If making any changes to hitchhiker.proto, you'll need the following to rebuild the python definitions:

```
brew install protobuf
pip3 install "grpclib[protobuf]"
pip3 install grpcio-tools
```

Then rebuild with:

```
python3 -m grpc_tools.protoc -I. --python_out=. --grpclib_python_out=. hitchhiker.proto
```