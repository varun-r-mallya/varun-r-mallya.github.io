.PHONY: hugo build serve clean

# Builds hugo from the vendored source in tools/hugo. Needs only the Go
# compiler - GOFLAGS=-mod=vendor and GOPROXY=off prove it never touches
# the network, so this keeps working even if the upstream Hugo project
# disappears.
hugo: bin/hugo

bin/hugo: tools/hugo/go.mod $(shell find tools/hugo -name '*.go' -not -path 'tools/hugo/vendor/*')
	mkdir -p bin
	cd tools/hugo && GOFLAGS=-mod=vendor GOPROXY=off GOSUMDB=off go build -o ../../bin/hugo .

build: hugo
	./bin/hugo --gc --minify

serve: hugo
	./bin/hugo server -D

clean:
	rm -rf bin public resources/_gen
