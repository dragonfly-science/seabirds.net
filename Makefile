clean:
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

test:
	cd seabirds && ./manage.py test cms profile
	
