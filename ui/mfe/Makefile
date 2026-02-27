# Build or dev all MFEs in parallel
MFES := fm-console pm-dashboard log-viewer snmp-ui ves-ui webhook-ui protobuf-ui sftp-avro-ui

.PHONY: install build dev

install:
	@for m in $(MFES); do echo "\n==> npm install $$m" && cd $$m && npm install && cd ..; done

build:
	@for m in $(MFES); do echo "\n==> build $$m" && cd $$m && npm run build && cd ..; done

dev:
	@for m in $(MFES); do cd $$m && npm run dev & cd ..; done
	wait
