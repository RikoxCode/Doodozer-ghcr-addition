FROM python:3.11-slim

WORKDIR /app

# Kopiere requirements und installiere Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Application Code
COPY . .

# Erstelle Download-Verzeichnis
RUN mkdir -p /downloads

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_PATH=/downloads

# Volume für Downloads
VOLUME ["/downloads"]

# Einstiegspunkt
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
