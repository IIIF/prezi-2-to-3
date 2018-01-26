FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
# Run tests:
RUN python setup.py test

CMD [ "prezi2to3.wsgi" ]
