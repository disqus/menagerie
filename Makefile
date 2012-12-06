ZOOKEEPER_VERSION=3.4.5

clean:
	find . -name *.pyc -delete

license:
	tail -14 LICENSE > LICENSE.short
	git ls-files | grep \.py$$ | xargs -n 1 bash bin/license.sh LICENSE.short
	rm LICENSE.short

lint:
	which pyflakes >/dev/null || pip install --use-mirrors pyflakes
	arc lint

test: clean
	python setup.py nosetests

test-matrix: clean
	which tox >/dev/null || pip install --use-mirrors tox
	tox

zookeeper:
	cd vendor/ && \
		wget https://github.com/apache/zookeeper/archive/release-$(ZOOKEEPER_VERSION).tar.gz && \
		tar xvf release-$(ZOOKEEPER_VERSION).tar.gz && \
		mv zookeeper-release-$(ZOOKEEPER_VERSION) zookeeper && \
		cd zookeeper && \
		ant

.PHONY: clean license lint test test-matrix zookeeper
