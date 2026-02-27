# MFE build helpers
# Run from repo root: make -C ui/mfe <target>
# Or from ui/mfe/: make <target>

MFES := snmp-ui ves-ui webhook-ui protobuf-ui sftp-avro-ui fm-console pm-dashboard log-viewer

.PHONY: install build dev clean $(MFES)

install:
	@for d in $(MFES); do echo "==> npm install $$d" && (cd $$d && npm install); done

build:
	@for d in $(MFES); do echo "==> build $$d" && (cd $$d && npm run build); done

clean:
	@for d in $(MFES); do rm -rf $$d/dist $$d/node_modules; done

# Individual targets
$(MFES):
	cd $@ && npm install && npm run build
