clean:
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

test:
	./runtests.sh
	
