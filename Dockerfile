FROM python:3.11-alpine as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1


# Install pipenv and compilation dependencies
RUN pip install pipenv && apk add gcc python3-dev openldap-dev libc-dev patchelf

# Install python dependencies in /.venv
COPY Pipfile Pipfile.lock ./
COPY src/ ./src/

RUN PIPENV_VENV_IN_PROJECT=1 pipenv install  && \
    pipenv install nuitka && \
    pipenv run python -m nuitka  --output-dir=out --follow-imports --standalone --onefile --include-package-data=selenium ./src/start.py


FROM alpine AS runtime


# Install application into container
# Copy virtual env from python-deps stage
COPY --from=base /out/start.bin  /book_reader/
COPY src/config.yaml src/config.template.yaml /book_reader/src/
COPY entrypoint.sh /book_reader/

WORKDIR /book_reader

# RUN chmod 777 ./start.bin


# 定义配置文件卷
VOLUME /book_reader/src/

# Run the application
ENTRYPOINT ["./start.bin"]

# run cdm
# run 命令使用 i t 参数  print 内容会实时刷新到 logs 内 设置时区
# docker run -dit --restart=always  -e TZ="Asia/Shanghai" -v ~/guahao/config:/home/appuser/app_guahao/config  --name=app_guahao wdjoys/guahao


#1