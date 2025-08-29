# ===== SEGMENT 1: Makefile vars & help =====
# Save as: Makefile   (use: `make help`)

# --- tweak these as needed ---
PORT    ?= COM5           # e.g., COM6 on Windows (use: PORT=COM6)
BAUD    ?= 115200
CLI     ?= python data_cli.py   # use "python" on Windows if needed
BANK    ?= human          # or: generated / GENERA~1
KEY     ?= A
SRC_DIR ?= ./human/A      # local folder to upload from
EXT     ?= mp3            # file extension (mp3/wav/ogg)

help:
	@echo "Usage:"
	@echo "  make ls                BANK=<human|generated> KEY=<A|SHIFT|...>"
	@echo "  make put FILE=001.mp3 PATH=./human/A/001.mp3"
	@echo "  make get FILE=001.mp3 OUT=./out/001.mp3"
	@echo "  make del FILE=001.mp3"
	@echo "  make upload-seq        (SRC_DIR -> 001/002/...)"
	@echo "  make upload-preserve   (SRC_DIR filenames preserved)"
	@echo "  make exit"
	@echo ""
	@echo "Defaults: PORT=$(PORT) BAUD=$(BAUD) BANK=$(BANK) KEY=$(KEY) SRC_DIR=$(SRC_DIR) EXT=$(EXT)"
	@echo "Remember: put /config/allow_writes.flag on the SD to enable PUT/DEL."

# ===== SEGMENT 2: Makefile single-file ops =====

ls:
	$(CLI) ls -p $(PORT) -b $(BAUD) $(BANK) $(KEY)

put:
	@if [ -z "$(FILE)" ] || [ -z "$(PATH)" ]; then \
	  echo "Usage: make put FILE=001.mp3 PATH=./local/001.mp3"; exit 2; fi
	$(CLI) put -p $(PORT) -b $(BAUD) $(BANK) $(KEY) $(FILE) $(PATH)

get:
	@if [ -z "$(FILE)" ] || [ -z "$(OUT)" ]; then \
	  echo "Usage: make get FILE=001.mp3 OUT=./out/001.mp3"; exit 2; fi
	@mkdir -p $$(dirname $(OUT))
	$(CLI) get -p $(PORT) -b $(BAUD) $(BANK) $(KEY) $(FILE) $(OUT)

del:
	@if [ -z "$(FILE)" ]; then \
	  echo "Usage: make del FILE=001.mp3"; exit 2; fi
	$(CLI) del -p $(PORT) -b $(BAUD) $(BANK) $(KEY) $(FILE)

exit:
	$(CLI) exit -p $(PORT) -b $(BAUD)

# ===== SEGMENT 3: Makefile folder ops =====

# Upload all *.$(EXT) in SRC_DIR as 001.$(EXT), 002.$(EXT), ...
upload-seq:
	@if [ ! -d "$(SRC_DIR)" ]; then echo "SRC_DIR not found: $(SRC_DIR)"; exit 2; fi
	@i=1; \
	find "$(SRC_DIR)" -maxdepth 1 -type f -name "*.$(EXT)" | sort | \
	while read -r f; do \
	  num=$$(printf "%03d" $$i); \
	  echo ">> PUT $$f -> $$num.$(EXT)"; \
	  $(CLI) put -p $(PORT) -b $(BAUD) $(BANK) $(KEY) $$num.$(EXT) "$$f" || exit $$?; \
	  i=$$((i+1)); \
	done

# Upload preserving local filenames
upload-preserve:
	@if [ ! -d "$(SRC_DIR)" ]; then echo "SRC_DIR not found: $(SRC_DIR)"; exit 2; fi
	@find "$(SRC_DIR)" -maxdepth 1 -type f -name "*.$(EXT)" | sort | \
	while read -r f; do \
	  base=$$(basename "$$f"); \
	  echo ">> PUT $$f -> $$base"; \
	  $(CLI) put -p $(PORT) -b $(BAUD) $(BANK) $(KEY) "$$base" "$$f" || exit $$?; \
	done

# ==== SEGMENT 3: Makefile sync-by-size targets ====

# Sync SRC_DIR to device as 001.ext, 002.ext... (only if missing or size differs)
sync-seq:
	$(CLI) sync-seq -p $(PORT) -b $(BAUD) --ext $(EXT) --start 1 $(BANK) $(KEY) $(SRC_DIR)

# Same, but keep original filenames on device
sync-preserve:
	$(CLI) sync-preserve -p $(PORT) -b $(BAUD) --ext $(EXT) $(BANK) $(KEY) $(SRC_DIR)

# Dry run previews:
sync-seq-dry:
	$(CLI) sync-seq -p $(PORT) -b $(BAUD) --ext $(EXT) --start 1 --dry-run $(BANK) $(KEY) $(SRC_DIR)

sync-preserve-dry:
	$(CLI) sync-preserve -p $(PORT) -b $(BAUD) --ext $(EXT) --dry-run $(BANK) $(KEY) $(SRC_DIR)

# ==== SEGMENT 4: Makefile examples (optional) ====
# make sync-seq        BANK=human KEY=A SRC_DIR=./human/A EXT=mp3 PORT=COM5
# make sync-preserve   BANK=generated KEY=SHIFT SRC_DIR=./generated/SHIFT EXT=mp3
# make sync-seq-dry    ... (preview without uploading)
