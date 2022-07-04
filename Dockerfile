FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080/tcp
CMD ["python", "./mini_healer_tools.py", "0.0.0.0", "8080"]
