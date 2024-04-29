.PHONY: dev, build, clean

clean:
	@rm -rf build

dev: clean
	@poetry run sphinx-autobuild source build

build: clean
	@poetry run sphinx-build source build
