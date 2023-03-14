
SRC=record.py request.py server.py env.py projectExceptions.py
REPORT=report.pdf

dist:
	tar -zcvf project.tgz ${SRC} ${REPORT}

clean:
	rm project.tgz