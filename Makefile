# Also needs to be updated in galaxy.yml
VERSION = 0.1.0

clean:
	rm -f kubernetes-core-${VERSION}.tar.gz

build: clean
	ansible-galaxy collection build

release: build
	ansible-galaxy collection publish kubernetes-core-${VERSION}.tar.gz

install: build
	ansible-galaxy collection install -p ansible_collections kubernetes-core-${VERSION}.tar.gz