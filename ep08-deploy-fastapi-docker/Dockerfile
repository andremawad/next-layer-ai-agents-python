# Pattern from the FastAPI docs: https://fastapi.tiangolo.com/deployment/docker/
FROM python:3.12-slim

WORKDIR /code

# dependencies first, so this layer stays cached when only the code changes
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./agent_core.py ./app.py /code/

# the key comes from the environment at run time, never from the image:
#   docker run -p 8000:80 -e OPENAI_API_KEY agent-api
CMD ["fastapi", "run", "app.py", "--port", "80"]
