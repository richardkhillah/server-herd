
SRC=record.py request.py server.py env.py
REPORT=report.pdf

dist:
	tar -zcvf project.tgz ${SRC} ${REPORT}

clean:
	rm project.tgz